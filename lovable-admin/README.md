# Lovable Admin - Database Maintenance System

## 🎯 Purpose
This directory contains the Lovable AI-generated database maintenance system for the Huapala Hawaiian Music Archives.

## 🏗️ Architecture
- **Isolated Environment**: Self-contained with its own dependencies
- **Neon Data API**: Direct PostgreSQL access via REST endpoints
- **Coordinated Operations**: Follows API_COORDINATION_GUIDE.md boundaries

## 📁 Directory Structure
```
lovable-admin/
├── README.md                 # This file
├── package.json             # Node.js dependencies
├── .env.example             # Environment configuration template
├── .gitignore              # Ignore sensitive files
├── src/
│   ├── components/         # React components for admin interface
│   ├── api/               # Neon Data API integration
│   ├── utils/             # Helper functions and utilities
│   └── styles/            # CSS/styling files
├── config/
│   ├── database.js        # Database configuration
│   └── neon-api.js        # Neon Data API setup
├── docs/
│   ├── api-reference.md   # API endpoint documentation
│   └── troubleshooting.md # Common issues and solutions
└── tests/
    ├── api.test.js        # API integration tests
    └── components.test.js # Component tests
```

## 🎯 Assigned Responsibilities
Based on API_COORDINATION_GUIDE.md, this system handles:

### ✅ Songbook Entries Management
- Create, read, update, delete songbook entries
- Basic filtering and sorting
- Simple pagination and search
- Form validation and submission

### ✅ UI Operations
- Admin dashboard for songbook maintenance
- Bulk editing interfaces
- Data entry forms
- Simple reporting and statistics

### ❌ NOT Handled Here
- Complex song data processing (handled by Railway API)
- Multi-table joins and complex queries
- Foreign key relationship management
- Business logic validation
- File processing and imports

## 🔗 Integration Points

### Railway API Coordination
- Complex operations are proxied to Railway API
- Foreign key operations use Railway endpoints
- Advanced search uses Railway search endpoints

### Database Access
- Direct access to `songbook_entries` table via Neon Data API
- Read-only access to other tables for reference data
- Respects existing foreign key constraints

## 🚀 Getting Started

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your Neon Data API credentials
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```

4. **Run tests**:
   ```bash
   npm test
   ```

## 📊 Key Features

### Songbook Management
- Add new songbook entries with validation
- Edit existing entries with inline editing
- Bulk operations for multiple entries
- Search and filter by various criteria

### Data Quality
- Basic validation and error checking
- Duplicate detection and prevention
- Data consistency reports
- Export capabilities for review

### User Interface
- Responsive design for desktop and mobile
- Intuitive forms and navigation
- Real-time updates and feedback
- Accessibility compliance

## 🔒 Security & Performance

### Access Control
- Environment-based configuration
- API rate limiting awareness
- Input sanitization and validation
- Error handling and logging

### Performance
- Efficient queries with proper indexing
- Pagination for large datasets
- Caching for reference data
- Optimized bundle size

## 📞 Support

### Troubleshooting
- Check docs/troubleshooting.md for common issues
- Verify environment configuration
- Test Neon Data API connectivity
- Review API_COORDINATION_GUIDE.md for boundaries

### Coordination with Railway API
- Use Railway API for complex operations
- Respect foreign key relationships
- Follow established data patterns
- Communicate schema changes

---

*This system is designed to work in harmony with the existing Railway API infrastructure while providing efficient database maintenance capabilities.*