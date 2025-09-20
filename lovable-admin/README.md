# Huapala Hawaiian Music Archives - Database Admin System

## 🎯 Purpose
This is the integrated Lovable AI + custom database administration system for the Huapala Hawaiian Music Archives. It provides a modern React interface for managing songbook entries while coordinating with the Railway API for complex operations.

## 🏗️ Architecture Integration

This system combines:
- **Lovable's Professional UI**: Modern React + TypeScript + shadcn-ui components
- **Our Database Integration**: Direct Neon Data API access for songbook entries
- **Railway API Coordination**: Complex operations and business logic

### System Boundaries
- ✅ **Full CRUD Operations**: Songbook entries management
- ✅ **UI/UX Interface**: Forms, tables, pagination, search
- ✅ **Data Validation**: Input validation and error handling
- ✅ **Reference Data**: Read-only access to canonical_mele and people tables
- ⚡ **Complex Operations**: Proxied to Railway API for multi-table operations

## 🚀 Getting Started

### Prerequisites
- Node.js & npm ([install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating))
- Access to Neon Database (configure in `.env`)

### Quick Start
```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Neon Data API credentials

# Start development server
npm run dev
# Opens at http://localhost:8080
```

### Production Build
```bash
npm run build
npm run preview
```

## 🎨 Technology Stack

### Frontend
- **Vite**: Fast build tool and dev server
- **React 18.3.1**: UI framework with hooks and modern patterns
- **TypeScript**: Type safety and better developer experience
- **Tailwind CSS**: Utility-first styling framework
- **shadcn-ui**: Professional, accessible component library
- **React Query**: State management and API caching
- **React Router**: Client-side routing

### Backend Integration
- **Neon Data API**: Direct PostgreSQL access via REST
- **Railway API**: Complex operations and business logic
- **Zod**: Runtime type validation

## 📁 Directory Structure

```
lovable-admin/
├── src/
│   ├── components/           # UI Components
│   │   ├── dashboard/       # Dashboard components
│   │   ├── forms/           # Form components
│   │   ├── mele/            # Song components  
│   │   ├── people/          # People components
│   │   ├── songs/           # Song list components
│   │   └── ui/              # shadcn-ui components
│   ├── lib/                 # Utilities and API
│   ├── pages/               # Page components
│   ├── types/               # TypeScript definitions
│   ├── data/                # Mock data and constants
│   └── hooks/               # Custom React hooks
├── config/                  # Database schema and config
├── docs/                    # API documentation
├── public/                  # Static assets
└── package.json             # Dependencies and scripts
```

## 🔗 API Integration Status

### ✅ Completed
- Professional React UI with shadcn-ui components
- Component structure for Dashboard, Songs, People, Forms
- Development environment setup
- TypeScript configuration

### 🚧 In Progress  
- Neon Data API integration layer
- Database schema validation
- Real API endpoints replacing mock data

### 📝 Planned
- Bulk operations for songbook entries
- Export/import functionality
- Advanced search and filtering
- Production deployment configuration

## 🛠️ Development

### Available Scripts
- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build
- `npm run lint`: Run ESLint

### Environment Configuration
Create `.env` file with:
```env
VITE_NEON_API_URL=your_neon_api_url
VITE_NEON_API_KEY=your_neon_api_key
VITE_RAILWAY_API_URL=your_railway_api_url
```

## 📊 Features

### Current Features (Lovable UI)
- 📱 **Responsive Dashboard**: Multi-tab interface for Songs, People, Add Entry
- 🎨 **Professional Design**: shadcn-ui components with consistent styling  
- 🔍 **Search Interface**: Placeholder for search functionality
- 📝 **Form Components**: Add entry forms with validation
- 📋 **Data Tables**: Song and people list views

### Planned Enhancements
- 🗄️ **Database Integration**: Real data from Neon PostgreSQL
- 🔄 **CRUD Operations**: Full create, read, update, delete for songbook entries
- 📤 **Bulk Operations**: Multi-select editing and batch updates
- 📊 **Data Validation**: Schema-based input validation
- 📈 **Analytics**: Usage statistics and data quality reports

## 🤝 Coordination with Main System

### Railway API Integration
For complex operations, this system coordinates with the Railway API:
- Multi-table joins and advanced queries
- Foreign key relationship management  
- Business logic validation
- File processing and imports

### Database Schema
Follows the established schema in `config/database-schema.json`:
- Primary table: `songbook_entries` (full access)
- Reference tables: `canonical_mele`, `people` (read-only)
- Respects foreign key constraints and validation rules

## 📞 Support & Documentation

### Documentation
- `docs/api-reference.md`: Comprehensive API endpoint documentation
- `docs/troubleshooting.md`: Common issues and solutions
- `config/database-schema.json`: Database structure and validation rules

### Lovable Integration
- **Original Project**: https://lovable.dev/projects/0db0f039-d876-4069-bbfd-9c369a06f115
- **Development**: Can continue using Lovable for UI enhancements
- **Local Development**: Full local development workflow supported

### Integration Status
This system successfully integrates Lovable's professional frontend with our custom database architecture, providing the best of both worlds: modern UI/UX and robust data management capabilities.

---

*Integrated system combining Lovable AI frontend excellence with custom database coordination for the Huapala Hawaiian Music Archives.*
