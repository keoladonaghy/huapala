# Lovable Integration Guide - Huapala Database Admin

## 🎯 Project Overview

You are creating a **database maintenance system** for the Huapala Hawaiian Music Archives project. This system will manage songbook entries through a clean, efficient admin interface.

## 📁 Your Workspace

You have access to the `lovable-admin/` directory within the Huapala GitHub repository. This is your dedicated space - you can create, modify, and organize files here without affecting the main system.

**Your Directory Structure:**
```
lovable-admin/
├── README.md                 # Your project documentation
├── package.json             # Dependencies and scripts  
├── .env.example             # Environment configuration template
├── .gitignore              # Git ignore rules
├── src/                    # Your React application
├── config/                 # Configuration files
├── docs/                   # API documentation
└── tests/                  # Your test files
```

## 🎯 Your Mission

### Primary Goal
Create a **songbook entries management system** that allows users to:
- Browse and search 2,109 songbook entries
- Add new songbook entries
- Edit existing entries
- Delete entries when needed
- View basic statistics and reports

### Database Focus
You'll primarily work with the **`songbook_entries`** table containing:
- Song titles (multiple variations)
- Songbook names and publication details
- Page numbers and composers
- Additional metadata and notes

## 🔗 Database Access

### Neon Data API
You'll use **Neon Data API** for direct PostgreSQL access:
- **Direct CRUD operations** on songbook entries
- **REST endpoints** for all database operations
- **Simple queries** with filtering and pagination
- **Real-time updates** for responsive UI

### Database Schema Reference
Check `config/database-schema.json` for complete table structure and validation rules.

## 🚫 System Boundaries

### ✅ What You Handle
- **Songbook entries CRUD** (Create, Read, Update, Delete)
- **Simple filtering and search** within songbook data
- **Form validation** and user input handling
- **Basic statistics** and reporting
- **Admin interface** design and user experience

### ❌ What You DON'T Handle
- **Complex song data processing** (handled by Railway API)
- **Multi-table joins** and complex queries
- **File uploads** and parsing
- **Foreign key relationships** (song linking)
- **Advanced search** across multiple tables

### 🔗 When to Use Railway API
For complex operations, proxy requests to the Railway API:
- Linking songbook entries to songs
- Advanced search across tables
- Complex validation and business logic

## 📊 Key Features to Build

### 1. Songbook Browser
- **Paginated table** showing all entries
- **Filter by**: songbook name, publication year, composer
- **Sort by**: any column (title, page, year, etc.)
- **Search**: simple text search within titles

### 2. Entry Editor
- **Form interface** for creating/editing entries
- **Field validation** (required fields, data types, ranges)
- **Dropdown lists** populated from reference data
- **Auto-save** functionality for better UX

### 3. Bulk Operations
- **Select multiple entries** for batch operations
- **Bulk edit** common fields (songbook, year, etc.)
- **Bulk delete** with confirmation
- **Import/export** capabilities

### 4. Dashboard
- **Statistics overview** (total entries, songbooks, etc.)
- **Recent activity** log
- **Data quality reports** (missing fields, duplicates)
- **Quick access** to common operations

## 🛠️ Technical Guidelines

### Frontend Framework
- **React** with modern hooks and patterns
- **Responsive design** for desktop and mobile
- **Accessible UI** with proper ARIA labels
- **Fast, intuitive navigation**

### Data Management
- **React Query** for server state management
- **Form handling** with react-hook-form
- **Real-time updates** and optimistic UI
- **Error handling** and loading states

### API Integration
- **Axios** for HTTP requests
- **Environment-based** configuration
- **Request queuing** to respect rate limits
- **Proper error handling** and retry logic

## 🚀 Getting Started

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Neon Data API credentials
# NEON_DATABASE_URL=postgresql://...
# NEON_API_KEY=your_api_key
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development
```bash
npm run dev
```

### 4. Build Your First Feature
Start with the **songbook browser** - a simple table showing entries with basic filtering.

## 📚 Resources

### Documentation
- `docs/api-reference.md` - Complete API endpoint documentation
- `config/database-schema.json` - Database structure and validation rules
- `../API_COORDINATION_GUIDE.md` - System integration guidelines

### Sample Data
The database contains 2,109 real songbook entries from Hawaiian music collections. Use these for testing and development.

### Reference Tables
- `canonical_mele` - Main song database (read-only reference)
- `people` - Contributors and composers (read-only reference)

## 🎨 Design Principles

### User Experience
- **Clean, intuitive interface** that doesn't overwhelm
- **Fast performance** with efficient queries
- **Clear feedback** for all user actions
- **Responsive design** that works on all devices

### Data Integrity
- **Validate all inputs** before submission
- **Prevent data loss** with auto-save features  
- **Clear error messages** when things go wrong
- **Confirmation dialogs** for destructive actions

### System Integration
- **Respect API boundaries** defined in coordination guide
- **Use Railway API** for complex operations when needed
- **Handle errors gracefully** when external APIs fail
- **Log important actions** for debugging

## 🏆 Success Metrics

Your system is successful when:
- ✅ Users can efficiently browse and search 2,109 songbook entries
- ✅ Adding/editing entries is fast and intuitive
- ✅ Data validation prevents errors and inconsistencies
- ✅ The interface is responsive and accessible
- ✅ Integration with existing systems is seamless

## 🤝 Collaboration

### With Claude Code (Railway API)
- Use coordination guide for API boundaries
- Proxy complex operations to Railway endpoints
- Respect foreign key relationships
- Communicate any schema change needs

### With Main Project
- Keep your code in `lovable-admin/` directory
- Follow existing naming conventions
- Document your API endpoints and patterns
- Test integration points thoroughly

---

**Ready to build an amazing database admin system!** 🎵🏝️

Start with the songbook browser feature and build from there. The foundation is solid, the data is rich, and the possibilities are endless!

*Questions? Check the docs or refer to the coordination guide for system boundaries.*