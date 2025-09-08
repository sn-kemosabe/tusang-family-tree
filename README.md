# TU SANG Family Tree Application

A comprehensive family tree management system built with Flask, MySQL, and modern web technologies.

## Features

### For Family Members (Non-Technical Users)
- **Simple Form Interface**: Easy-to-use form for adding family member information
- **User-Friendly Design**: Clean, intuitive interface with helpful tips and guidance
- **No Technical Knowledge Required**: Anyone can contribute to the family tree
- **Mobile Responsive**: Works on phones, tablets, and computers

### For Administrators
- **Admin Dashboard**: Complete management interface for data oversight
- **Data Validation**: Tools to verify and correct family information
- **Relationship Management**: Create and manage family connections
- **Export Capabilities**: Generate reports and export data
- **Print Functionality**: Create printable family trees

### Core Functionality
- **Family Member Profiles**: Store comprehensive information about each family member
- **Relationship Mapping**: Track parent-child, spouse, and sibling relationships
- **Interactive Family Tree**: Visual representation of family connections
- **Printable Output**: Generate beautiful family tree diagrams for printing
- **Data Security**: Secure login system for administrators

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package installer)

### Step 1: Clone/Download the Project
```bash
cd /path/to/your/projects
# If using git:
# git clone <repository-url> tusang-family-tree
# cd tusang-family-tree
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Setup
1. **Install MySQL** (if not already installed)
2. **Create Database**:
   ```sql
   CREATE DATABASE family_tree;
   CREATE USER 'family_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON family_tree.* TO 'family_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Update Database Configuration** in `app.py`:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://family_user:your_password@localhost/family_tree'
   ```

### Step 5: Initialize Database
```bash
# Initialize Flask-Migrate
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### Step 6: Create Admin User
```bash
python -c "
from app import app, db, User
with app.app_context():
    admin = User(username='admin', email='admin@family.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created: username=admin, password=admin123')
"
```

### Step 7: Run the Application
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

## Usage Guide

### For Family Members
1. **Visit the Homepage**: Navigate to `http://localhost:5000`
2. **Add Family Member**: Click "Add Family Member" button
3. **Fill the Form**: Enter as much information as you know
4. **Submit**: Click "Save Family Member" to submit
5. **View Tree**: Click "View Family Tree" to see the growing family tree

### For Administrators
1. **Login**: Click "Admin Login" and use your credentials
2. **Manage Data**: View, edit, and validate family member information
3. **Create Relationships**: Link family members together
4. **Generate Reports**: Export data and create printable family trees
5. **System Management**: Backup data and maintain the system

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=mysql://username:password@localhost/family_tree
FLASK_ENV=development
```

### Database Configuration
Update the database connection string in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/family_tree'
```

## File Structure
```
tusang-family-tree/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Homepage
│   ├── family_form.html  # Add family member form
│   ├── family_tree.html  # Family tree visualization
│   ├── login.html        # Admin login
│   └── admin_dashboard.html # Admin interface
├── static/               # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # JavaScript functionality
└── migrations/           # Database migrations (created after setup)
```

## API Endpoints

### Public Endpoints
- `GET /` - Homepage
- `GET /family-form` - Add family member form
- `GET /family-tree` - View family tree
- `POST /api/add-member` - Add new family member
- `GET /api/get-members` - Get all family members
- `GET /api/family-tree-data` - Get family tree data

### Admin Endpoints
- `GET /login` - Admin login page
- `POST /login` - Process login
- `GET /admin` - Admin dashboard
- `POST /api/add-relationship` - Add family relationship

## Customization

### Adding New Fields
1. Update the `FamilyMember` model in `app.py`
2. Create a new migration: `flask db migrate -m "Add new field"`
3. Apply migration: `flask db upgrade`
4. Update the form template and API endpoints

### Styling
- Modify `static/css/style.css` for custom styling
- Update Bootstrap classes in templates for different themes

### Database
- Change database type by updating SQLAlchemy URI
- Modify models in `app.py` for different data structures

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify MySQL is running
   - Check database credentials
   - Ensure database exists

2. **Import Errors**
   - Activate virtual environment
   - Install all requirements: `pip install -r requirements.txt`

3. **Permission Errors**
   - Check file permissions
   - Ensure database user has proper privileges

4. **Port Already in Use**
   - Change port in `app.py`: `app.run(debug=True, port=5001)`

### Getting Help
- Check Flask documentation: https://flask.palletsprojects.com/
- MySQL documentation: https://dev.mysql.com/doc/
- Bootstrap documentation: https://getbootstrap.com/docs/

## Security Notes

- Change default admin password immediately
- Use strong, unique passwords
- Keep dependencies updated
- Use HTTPS in production
- Regular database backups recommended

## License

This project is created for the TU SANG family. Please respect privacy and data protection guidelines.

## Support

For technical support or questions about the family tree application, contact the system administrator.
