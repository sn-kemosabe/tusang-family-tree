from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
import uuid
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
# For easy setup, using SQLite (no MySQL required)
# Change to 'mysql+pymysql://username:password@localhost/family_tree' for MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///family_tree.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration for persistent logins
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Photo upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class FamilyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    chinese_name = db.Column(db.String(100))
    nickname = db.Column(db.String(100))
    birth_date = db.Column(db.Date)
    death_date = db.Column(db.Date)
    birth_place = db.Column(db.String(200))
    death_place = db.Column(db.String(200))
    gender = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text)
    photo_filename = db.Column(db.String(500))
    is_alive = db.Column(db.Boolean, default=True)
    
    # New fields for marital status and family information
    marital_status = db.Column(db.String(20))  # Single, Married
    father_name = db.Column(db.String(200))
    mother_name = db.Column(db.String(200))
    spouse_name = db.Column(db.String(200))
    have_children = db.Column(db.String(10))  # Yes, No
    children_data = db.Column(db.Text)  # JSON string for children information
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent_relationships = db.relationship('FamilyRelationship', 
                                         foreign_keys='FamilyRelationship.child_id',
                                         backref='child', lazy='dynamic')
    child_relationships = db.relationship('FamilyRelationship',
                                        foreign_keys='FamilyRelationship.parent_id', 
                                        backref='parent', lazy='dynamic')

class FamilyRelationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('family_member.id'), nullable=False)
    relationship_type = db.Column(db.String(50), nullable=False)  # 'parent', 'spouse', 'sibling'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(file):
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return unique_filename
    return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard' if current_user.is_admin else 'family_form'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember_me = request.form.get('remember_me') == 'on'  # Checkbox value
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember_me)  # Remember based on checkbox
            return redirect(url_for('admin_dashboard' if user.is_admin else 'family_form'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/family-form')
def family_form():
    return render_template('family_form.html')

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied')
        return redirect(url_for('family_form'))
    
    members = FamilyMember.query.all()
    return render_template('admin_dashboard.html', members=members)

@app.route('/api/add-member', methods=['POST'])
def add_family_member():
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            photo_filename = None
        else:
            data = request.form.to_dict()
            # Handle photo upload
            photo_file = request.files.get('photo')
            photo_filename = save_photo(photo_file) if photo_file else None
        
        # Process children data if present
        children_data = None
        if 'children_data' in data:
            children_data = json.dumps(data['children_data']) if data['children_data'] else None
        
        # Convert is_alive to boolean
        is_alive = data.get('is_alive', 'true').lower() == 'true'
        
        member = FamilyMember(
            full_name=data['full_name'],
            chinese_name=data.get('chinese_name', ''),
            nickname=data.get('nickname', ''),
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else None,
            death_date=datetime.strptime(data['death_date'], '%Y-%m-%d').date() if data.get('death_date') else None,
            birth_place=data.get('birth_place', ''),
            death_place=data.get('death_place', ''),
            gender=data['gender'],
            notes=data.get('notes', ''),
            photo_filename=photo_filename,
            is_alive=is_alive,
            # New fields
            marital_status=data.get('marital_status', ''),
            father_name=data.get('father_name', ''),
            mother_name=data.get('mother_name', ''),
            spouse_name=data.get('spouse_name', ''),
            have_children=data.get('have_children', ''),
            children_data=children_data
        )
        
        db.session.add(member)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Family member added successfully', 'id': member.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/get-members')
def get_family_members():
    members = FamilyMember.query.all()
    return jsonify([{
        'id': member.id,
        'full_name': member.full_name,
        'chinese_name': member.chinese_name,
        'nickname': member.nickname,
        'birth_date': member.birth_date.isoformat() if member.birth_date else None,
        'death_date': member.death_date.isoformat() if member.death_date else None,
        'birth_place': member.birth_place,
        'death_place': member.death_place,
        'gender': member.gender,
        'notes': member.notes,
        'photo_filename': member.photo_filename,
        'is_alive': member.is_alive,
        'marital_status': member.marital_status,
        'father_name': member.father_name,
        'mother_name': member.mother_name,
        'spouse_name': member.spouse_name,
        'have_children': member.have_children,
        'children_data': member.children_data,
        'created_at': member.created_at.isoformat()
    } for member in members])

@app.route('/api/get-member/<int:member_id>')
def get_family_member(member_id):
    member = FamilyMember.query.get_or_404(member_id)
    return jsonify({
        'id': member.id,
        'full_name': member.full_name,
        'chinese_name': member.chinese_name,
        'nickname': member.nickname,
        'birth_date': member.birth_date.isoformat() if member.birth_date else None,
        'death_date': member.death_date.isoformat() if member.death_date else None,
        'birth_place': member.birth_place,
        'death_place': member.death_place,
        'gender': member.gender,
        'notes': member.notes,
        'photo_filename': member.photo_filename,
        'is_alive': member.is_alive,
        'marital_status': member.marital_status,
        'father_name': member.father_name,
        'mother_name': member.mother_name,
        'spouse_name': member.spouse_name,
        'have_children': member.have_children,
        'children_data': member.children_data,
        'created_at': member.created_at.isoformat()
    })

@app.route('/api/update-member/<int:member_id>', methods=['PUT', 'POST'])
def update_family_member(member_id):
    try:
        member = FamilyMember.query.get_or_404(member_id)
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            photo_filename = member.photo_filename  # Keep existing photo if no new one
        else:
            data = request.form.to_dict()
            # Handle photo upload
            photo_file = request.files.get('photo')
            photo_filename = save_photo(photo_file) if photo_file else member.photo_filename
        
        # Process children data if present
        children_data = None
        if 'children_data' in data:
            children_data = json.dumps(data['children_data']) if data['children_data'] else None
        
        # Convert is_alive to boolean
        is_alive = data.get('is_alive', 'true').lower() == 'true'
        
        # Update member fields
        member.full_name = data['full_name']
        member.chinese_name = data.get('chinese_name', '')
        member.nickname = data.get('nickname', '')
        member.birth_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date() if data.get('birth_date') else None
        member.death_date = datetime.strptime(data['death_date'], '%Y-%m-%d').date() if data.get('death_date') else None
        member.birth_place = data.get('birth_place', '')
        member.death_place = data.get('death_place', '')
        member.gender = data['gender']
        member.notes = data.get('notes', '')
        member.photo_filename = photo_filename
        member.is_alive = is_alive
        member.marital_status = data.get('marital_status', '')
        member.father_name = data.get('father_name', '')
        member.mother_name = data.get('mother_name', '')
        member.spouse_name = data.get('spouse_name', '')
        member.have_children = data.get('have_children', '')
        member.children_data = children_data
        member.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Family member updated successfully', 'id': member.id})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/delete-member/<int:member_id>', methods=['DELETE', 'POST'])
def delete_family_member(member_id):
    try:
        member = FamilyMember.query.get_or_404(member_id)
        
        # Delete associated relationships first
        FamilyRelationship.query.filter_by(parent_id=member_id).delete()
        FamilyRelationship.query.filter_by(child_id=member_id).delete()
        
        # Delete the member
        db.session.delete(member)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Family member deleted successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/check-existing-names', methods=['POST'])
def check_existing_names():
    try:
        data = request.get_json()
        full_name = data.get('full_name', '').strip()
        
        if not full_name:
            return jsonify({'success': False, 'message': 'Full name is required'})
        
        # Check for exact matches
        exact_matches = FamilyMember.query.filter(
            FamilyMember.full_name.ilike(f'%{full_name}%')
        ).all()
        
        # Check for similar names (fuzzy matching)
        similar_matches = FamilyMember.query.filter(
            db.or_(
                FamilyMember.nickname.ilike(f'%{full_name}%'),
                FamilyMember.chinese_name.ilike(f'%{full_name}%')
            )
        ).all()
        
        # Combine and deduplicate results
        all_matches = list(set(exact_matches + similar_matches))
        
        matches_data = []
        for member in all_matches:
            matches_data.append({
                'id': member.id,
                'full_name': member.full_name,
                'chinese_name': member.chinese_name,
                'nickname': member.nickname,
                'gender': member.gender,
                'birth_date': member.birth_date.isoformat() if member.birth_date else None,
                'is_alive': member.is_alive
            })
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'count': len(matches_data)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/suggest-relationships', methods=['POST'])
def suggest_relationships():
    try:
        data = request.get_json()
        member_id = data.get('member_id')
        father_name = data.get('father_name', '').strip()
        mother_name = data.get('mother_name', '').strip()
        spouse_name = data.get('spouse_name', '').strip()
        
        suggestions = []
        
        # Check for father
        if father_name:
            father_matches = FamilyMember.query.filter(
                FamilyMember.full_name.ilike(f'%{father_name}%')
            ).all()
            for match in father_matches:
                suggestions.append({
                    'type': 'parent',
                    'relationship': 'father',
                    'member': {
                        'id': match.id,
                        'full_name': match.full_name,
                        'chinese_name': match.chinese_name,
                        'nickname': match.nickname,
                        'gender': match.gender
                    }
                })
        
        # Check for mother
        if mother_name:
            mother_matches = FamilyMember.query.filter(
                FamilyMember.full_name.ilike(f'%{mother_name}%')
            ).all()
            for match in mother_matches:
                suggestions.append({
                    'type': 'parent',
                    'relationship': 'mother',
                    'member': {
                        'id': match.id,
                        'full_name': match.full_name,
                        'chinese_name': match.chinese_name,
                        'nickname': match.nickname,
                        'gender': match.gender
                    }
                })
        
        # Check for spouse
        if spouse_name:
            spouse_matches = FamilyMember.query.filter(
                FamilyMember.full_name.ilike(f'%{spouse_name}%')
            ).all()
            for match in spouse_matches:
                suggestions.append({
                    'type': 'spouse',
                    'relationship': 'spouse',
                    'member': {
                        'id': match.id,
                        'full_name': match.full_name,
                        'chinese_name': match.chinese_name,
                        'nickname': match.nickname,
                        'gender': match.gender
                    }
                })
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/create-relationship', methods=['POST'])
def create_relationship():
    try:
        data = request.get_json()
        member_id = data.get('member_id')
        related_member_id = data.get('related_member_id')
        relationship_type = data.get('relationship_type')  # 'parent', 'spouse', 'sibling'
        
        if not all([member_id, related_member_id, relationship_type]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Check if relationship already exists
        existing = FamilyRelationship.query.filter(
            db.or_(
                db.and_(FamilyRelationship.parent_id == member_id, FamilyRelationship.child_id == related_member_id),
                db.and_(FamilyRelationship.parent_id == related_member_id, FamilyRelationship.child_id == member_id)
            )
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Relationship already exists'})
        
        # Create relationship
        if relationship_type == 'parent':
            relationship = FamilyRelationship(
                parent_id=related_member_id,
                child_id=member_id,
                relationship_type='parent'
            )
        elif relationship_type == 'spouse':
            # For spouse relationships, we'll create bidirectional
            relationship1 = FamilyRelationship(
                parent_id=member_id,
                child_id=related_member_id,
                relationship_type='spouse'
            )
            relationship2 = FamilyRelationship(
                parent_id=related_member_id,
                child_id=member_id,
                relationship_type='spouse'
            )
            db.session.add(relationship1)
            db.session.add(relationship2)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Spouse relationship created successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid relationship type'})
        
        db.session.add(relationship)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Relationship created successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/add-relationship', methods=['POST'])
def add_relationship():
    try:
        data = request.get_json()
        
        relationship = FamilyRelationship(
            parent_id=data['parent_id'],
            child_id=data['child_id'],
            relationship_type=data['relationship_type']
        )
        
        db.session.add(relationship)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Relationship added successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/family-tree')
def family_tree():
    return render_template('family_tree.html')

@app.route('/api/family-tree-data')
def get_family_tree_data():
    # This will be implemented to generate tree structure
    members = FamilyMember.query.all()
    relationships = FamilyRelationship.query.all()
    
    tree_data = {
        'members': [{
            'id': member.id,
            'full_name': member.full_name,
            'chinese_name': member.chinese_name,
            'nickname': member.nickname,
            'birth_date': member.birth_date.isoformat() if member.birth_date else None,
            'death_date': member.death_date.isoformat() if member.death_date else None,
            'gender': member.gender,
            'current_status': 'Living' if member.is_alive else 'Deceased',
            'photo_filename': member.photo_filename
        } for member in members],
        'relationships': [{
            'parent_id': rel.parent_id,
            'child_id': rel.child_id,
            'type': rel.relationship_type
        } for rel in relationships]
    }
    
    return jsonify(tree_data)

@app.route('/api/convert-children-to-members', methods=['POST'])
def convert_children_to_members():
    """Convert all children data stored in children_data field to separate family member records"""
    try:
        # Get all members who have children data
        members_with_children = FamilyMember.query.filter(
            FamilyMember.children_data.isnot(None),
            FamilyMember.children_data != '',
            FamilyMember.children_data != '[]'
        ).all()
        
        converted_count = 0
        new_member_ids = []
        
        for parent in members_with_children:
            try:
                children_data = json.loads(parent.children_data)
                if not children_data or not isinstance(children_data, list):
                    continue
                
                for child_data in children_data:
                    # Check if child already exists (by full name)
                    existing_child = FamilyMember.query.filter_by(full_name=child_data.get('full_name', '')).first()
                    if existing_child:
                        continue  # Skip if child already exists
                    
                    # Create new family member for child
                    child_member = FamilyMember(
                        full_name=child_data.get('full_name', ''),
                        chinese_name=child_data.get('chinese_name', ''),
                        nickname=child_data.get('nickname', ''),
                        birth_date=datetime.strptime(child_data.get('birth_date', ''), '%Y-%m-%d').date() if child_data.get('birth_date') else None,
                        birth_place='',  # Not stored in children_data
                        death_date=None,  # Children are typically alive
                        death_place='',
                        gender=child_data.get('gender', ''),
                        notes=f"Child of {parent.full_name}",
                        photo_filename=None,
                        is_alive=True,  # Children are typically alive
                        marital_status='Single',  # Default for children
                        father_name=parent.full_name if parent.gender == 'Male' else '',
                        mother_name=parent.full_name if parent.gender == 'Female' else '',
                        spouse_name='',
                        have_children='No',
                        children_data=None
                    )
                    
                    db.session.add(child_member)
                    db.session.flush()  # Get the ID
                    
                    # Create parent-child relationship
                    relationship = FamilyRelationship(
                        parent_id=parent.id,
                        child_id=child_member.id,
                        relationship_type='parent'
                    )
                    db.session.add(relationship)
                    
                    new_member_ids.append(child_member.id)
                    converted_count += 1
                
                # Clear children_data from parent after conversion
                parent.children_data = None
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"Error processing children data for member {parent.id}: {e}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully converted {converted_count} children to separate family members',
            'new_member_ids': new_member_ids,
            'converted_count': converted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error converting children: {str(e)}'}), 500

@app.route('/api/convert-spouses-to-members', methods=['POST'])
def convert_spouses_to_members():
    """Convert all spouse names stored in spouse_name field to separate family member records"""
    try:
        # Get all members who have spouse names
        members_with_spouses = FamilyMember.query.filter(
            FamilyMember.spouse_name.isnot(None),
            FamilyMember.spouse_name != '',
            FamilyMember.spouse_name != 'undefined'
        ).all()
        
        converted_count = 0
        new_member_ids = []
        
        for member in members_with_spouses:
            spouse_name = member.spouse_name.strip()
            if not spouse_name:
                continue
            
            # Check if spouse already exists (by full name)
            existing_spouse = FamilyMember.query.filter_by(full_name=spouse_name).first()
            if existing_spouse:
                # If spouse exists, create spouse relationship if it doesn't exist
                existing_spouse_rel = FamilyRelationship.query.filter(
                    ((FamilyRelationship.parent_id == member.id) & (FamilyRelationship.child_id == existing_spouse.id)) |
                    ((FamilyRelationship.parent_id == existing_spouse.id) & (FamilyRelationship.child_id == member.id))
                ).first()
                
                if not existing_spouse_rel:
                    # Create spouse relationship
                    spouse_relationship = FamilyRelationship(
                        parent_id=member.id,
                        child_id=existing_spouse.id,
                        relationship_type='spouse'
                    )
                    db.session.add(spouse_relationship)
                    converted_count += 1
                continue
            
            # Determine spouse gender (opposite of current member)
            spouse_gender = 'Female' if member.gender == 'Male' else 'Male'
            
            # Create new family member for spouse
            spouse_member = FamilyMember(
                full_name=spouse_name,
                chinese_name='',  # Not available in spouse_name field
                nickname='',  # Not available in spouse_name field
                birth_date=None,  # Not available
                birth_place='',  # Not available
                death_date=None,  # Unknown status
                death_place='',
                gender=spouse_gender,
                notes=f"Spouse of {member.full_name}",
                photo_filename=None,
                is_alive=True,  # Default assumption
                marital_status='Married',
                father_name='',  # Not available
                mother_name='',  # Not available
                spouse_name=member.full_name,  # Link back to original member
                have_children='',  # Unknown
                children_data=None
            )
            
            db.session.add(spouse_member)
            db.session.flush()  # Get the ID
            
            # Create spouse relationship
            spouse_relationship = FamilyRelationship(
                parent_id=member.id,
                child_id=spouse_member.id,
                relationship_type='spouse'
            )
            db.session.add(spouse_relationship)
            
            new_member_ids.append(spouse_member.id)
            converted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully converted {converted_count} spouses to separate family members',
            'new_member_ids': new_member_ids,
            'converted_count': converted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error converting spouses: {str(e)}'}), 500

@app.route('/api/export-gedcom', methods=['GET'])
def export_gedcom():
    try:
        members = FamilyMember.query.all()
        relationships = FamilyRelationship.query.all()
        
        # Create GEDCOM content
        gedcom_content = generate_gedcom(members, relationships)
        
        # Create response with GEDCOM file
        response = make_response(gedcom_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = 'attachment; filename=family_tree.ged'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_gedcom(members, relationships):
    """Generate GEDCOM format from family data"""
    gedcom_lines = []
    
    # GEDCOM header
    gedcom_lines.append("0 HEAD")
    gedcom_lines.append("1 SOUR TU SANG Family Tree")
    gedcom_lines.append("2 NAME TU SANG Family Tree Application")
    gedcom_lines.append("2 VERS 1.0")
    gedcom_lines.append("1 DEST ANSTFILE")
    gedcom_lines.append("1 DATE " + datetime.now().strftime("%d %b %Y"))
    gedcom_lines.append("1 GEDC")
    gedcom_lines.append("2 VERS 5.5.1")
    gedcom_lines.append("2 FORM LINEAGE-LINKED")
    gedcom_lines.append("1 CHAR UTF-8")
    gedcom_lines.append("0 @SUBM@ SUBM")
    gedcom_lines.append("1 NAME TU SANG Family")
    gedcom_lines.append("")
    
    # Create individual records
    for member in members:
        individual_id = f"@I{member.id:03d}@"
        gedcom_lines.append(f"0 {individual_id} INDI")
        
        # Name
        if member.full_name:
            gedcom_lines.append(f"1 NAME {member.full_name}")
            if member.chinese_name:
                gedcom_lines.append(f"2 GIVN {member.chinese_name}")
            if member.nickname:
                gedcom_lines.append(f"2 NICK {member.nickname}")
        
        # Gender
        if member.gender:
            gender_code = "M" if member.gender == "Male" else "F"
            gedcom_lines.append(f"1 SEX {gender_code}")
        
        # Birth
        if member.birth_date:
            birth_date = member.birth_date.strftime("%d %b %Y")
            gedcom_lines.append(f"1 BIRT")
            gedcom_lines.append(f"2 DATE {birth_date}")
            if member.birth_place:
                gedcom_lines.append(f"2 PLAC {member.birth_place}")
        
        # Death
        if not member.is_alive and member.death_date:
            death_date = member.death_date.strftime("%d %b %Y")
            gedcom_lines.append(f"1 DEAT")
            gedcom_lines.append(f"2 DATE {death_date}")
            if member.death_place:
                gedcom_lines.append(f"2 PLAC {member.death_place}")
        
        # Notes
        if member.notes:
            gedcom_lines.append(f"1 NOTE {member.notes}")
        
        gedcom_lines.append("")
    
    # Create family records
    family_groups = {}
    for rel in relationships:
        if rel.relationship_type == 'spouse':
            # Create family group for spouses
            family_key = tuple(sorted([rel.parent_id, rel.child_id]))
            if family_key not in family_groups:
                family_groups[family_key] = {
                    'husband': None,
                    'wife': None,
                    'children': []
                }
            
            # Determine husband and wife
            parent = next((m for m in members if m.id == rel.parent_id), None)
            child = next((m for m in members if m.id == rel.child_id), None)
            
            if parent and child:
                if parent.gender == 'Male':
                    family_groups[family_key]['husband'] = parent.id
                    family_groups[family_key]['wife'] = child.id
                else:
                    family_groups[family_key]['husband'] = child.id
                    family_groups[family_key]['wife'] = parent.id
        
        elif rel.relationship_type == 'parent':
            # Add child to family group
            family_key = tuple(sorted([rel.parent_id, rel.child_id]))
            if family_key not in family_groups:
                family_groups[family_key] = {
                    'husband': None,
                    'wife': None,
                    'children': []
                }
            
            # Find the spouse of the parent to create proper family group
            spouse_rel = next((r for r in relationships 
                            if r.relationship_type == 'spouse' 
                            and (r.parent_id == rel.parent_id or r.child_id == rel.parent_id)), None)
            
            if spouse_rel:
                spouse_id = spouse_rel.child_id if spouse_rel.parent_id == rel.parent_id else spouse_rel.parent_id
                family_key = tuple(sorted([rel.parent_id, spouse_id]))
                if family_key not in family_groups:
                    family_groups[family_key] = {
                        'husband': None,
                        'wife': None,
                        'children': []
                    }
                
                parent = next((m for m in members if m.id == rel.parent_id), None)
                spouse = next((m for m in members if m.id == spouse_id), None)
                
                if parent and spouse:
                    if parent.gender == 'Male':
                        family_groups[family_key]['husband'] = parent.id
                        family_groups[family_key]['wife'] = spouse.id
                    else:
                        family_groups[family_key]['husband'] = spouse.id
                        family_groups[family_key]['wife'] = parent.id
            
            family_groups[family_key]['children'].append(rel.child_id)
    
    # Write family records
    family_id = 1
    for family_key, family_data in family_groups.items():
        if family_data['husband'] or family_data['wife'] or family_data['children']:
            family_record_id = f"@F{family_id:03d}@"
            gedcom_lines.append(f"0 {family_record_id} FAM")
            
            if family_data['husband']:
                gedcom_lines.append(f"1 HUSB @I{family_data['husband']:03d}@")
            if family_data['wife']:
                gedcom_lines.append(f"1 WIFE @I{family_data['wife']:03d}@")
            
            for child_id in family_data['children']:
                gedcom_lines.append(f"1 CHIL @I{child_id:03d}@")
            
            gedcom_lines.append("")
            family_id += 1
    
    # Add individual family links
    for family_key, family_data in family_groups.items():
        if family_data['husband']:
            gedcom_lines.append(f"0 @I{family_data['husband']:03d}@ INDI")
            gedcom_lines.append(f"1 FAMS @F{family_id-1:03d}@")
        if family_data['wife']:
            gedcom_lines.append(f"0 @I{family_data['wife']:03d}@ INDI")
            gedcom_lines.append(f"1 FAMS @F{family_id-1:03d}@")
        for child_id in family_data['children']:
            gedcom_lines.append(f"0 @I{child_id:03d}@ INDI")
            gedcom_lines.append(f"1 FAMC @F{family_id-1:03d}@")
    
    # GEDCOM trailer
    gedcom_lines.append("0 TRLR")
    
    return "\n".join(gedcom_lines)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
