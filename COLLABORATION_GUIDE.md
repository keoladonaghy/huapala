# Collaboration Guide - Huapala Repository

## 🤝 For Lovable AI Team

Welcome to the Huapala Hawaiian Music Archives repository! This guide will help you get started working on the database admin interface.

### 🎯 Your Scope
You'll be working exclusively in the **`lovable-admin/` directory**, which contains a complete React + TypeScript application for database administration.

### 📁 Directory Structure
```
huapala/
├── lovable-admin/          ← YOUR WORKSPACE
│   ├── src/                ← React application
│   ├── package.json        ← Dependencies
│   ├── vite.config.ts      ← Build configuration
│   ├── .env.example        ← Environment template
│   └── README.md           ← Your app documentation
├── main.py                 ← Owner's API (don't modify)
├── scripts/                ← Owner's processing scripts
└── docs/                   ← Shared documentation
```

### 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/keoladonaghy/huapala.git
   cd huapala/lovable-admin
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start development**:
   ```bash
   npm run dev
   # Opens at http://localhost:8080
   ```

### 🔧 Development Workflow

**Daily Workflow:**
```bash
# Always work in the lovable-admin directory
cd lovable-admin/

# Pull latest changes
git pull origin main

# Make your changes to React components
# Work in src/ directory

# Test your changes
npm run dev

# Commit your work
git add .
git commit -m "feat: add new admin feature"
git push origin main
```

**File Modification Guidelines:**
- ✅ **Modify freely**: Everything in `lovable-admin/src/`
- ✅ **Update**: `package.json` for new dependencies
- ✅ **Configure**: Vite, TypeScript, Tailwind configs
- ❌ **Don't touch**: Files outside `lovable-admin/` directory
- ❌ **Don't modify**: Root `main.py`, `requirements.txt`, Railway configs

### 🗄️ Database Integration

**What You Need to Know:**
- **Primary Table**: `songbook_entries` (full CRUD access)
- **Reference Tables**: `canonical_mele`, `people` (read-only)
- **API Access**: Direct Neon Data API for simple operations
- **Complex Operations**: Proxy to Railway API when needed

**Database Schema:**
Check `config/database-schema.json` for complete table structures and validation rules.

**API Patterns:**
Check `docs/api-reference.md` for endpoint documentation and usage examples.

### 🔗 API Integration Points

**Neon Data API (Primary):**
```typescript
// Direct database operations
const response = await fetch(`${VITE_NEON_API_URL}/songbook_entries`, {
  headers: { 'Authorization': `Bearer ${VITE_NEON_API_KEY}` }
});
```

**Railway API (Complex Operations):**
```typescript
// For linking songs to entries, complex searches
const response = await fetch(`${VITE_RAILWAY_API_URL}/link-song-songbook`, {
  method: 'POST',
  body: JSON.stringify({ songId, entryId })
});
```

### 🚀 Deployment

Your admin interface deploys **separately** from the main application:

**Recommended Platforms:**
1. **Vercel** (React-optimized, included config: `vercel.json`)
2. **Netlify** (Great for static sites, included config: `netlify.toml`)
3. **Railway** (Separate service from main app)

**Deployment Steps:**
1. Connect your preferred platform to this repository
2. Set build directory to: `lovable-admin/`
3. Configure environment variables from `.env.example`
4. Deploy!

**Environment Variables for Production:**
```
VITE_NEON_API_URL=https://your-project.neon.tech/api/v1
VITE_NEON_API_KEY=your_production_key
VITE_RAILWAY_API_URL=https://web-production-cde73.up.railway.app
```

### 🎨 Current Tech Stack

**Frontend:**
- **Vite**: Fast build tool
- **React 18.3.1**: UI framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **shadcn-ui**: Component library
- **React Query**: State management

**Components Already Built:**
- Dashboard with multiple tabs
- Song list and management
- People/artist management
- Add entry forms
- Search interface (placeholder)
- Settings (placeholder)

### 📋 Your Mission

**Primary Goals:**
1. **Connect real data**: Replace mock data with actual Neon API calls
2. **Implement CRUD**: Full create, read, update, delete for songbook entries
3. **Add bulk operations**: Multi-select editing and batch updates
4. **Enhance forms**: Add validation matching database schema
5. **Improve UX**: Polish the interface for production use

**Current Status:**
- ✅ Professional UI components built
- ✅ Routing and navigation working
- ✅ Development environment ready
- 🚧 Mock data needs replacement with real API
- 🚧 Form validation needs database schema integration
- 📝 Bulk operations need implementation

### 🤝 Coordination

**Communication:**
- Use GitHub issues for feature requests or questions
- Tag repository owner (@keoladonaghy) for database/API questions
- Document any new environment variables needed

**When You Need Help:**
- **Database Questions**: Check `docs/api-reference.md` first
- **Schema Questions**: Reference `config/database-schema.json`
- **API Issues**: Ask repository owner about Railway API coordination
- **Deployment Issues**: Repository owner can help with platform setup

**What We Handle:**
- Main Python API maintenance and complex business logic
- Database schema changes and migrations
- Railway deployment and infrastructure
- Song processing and data imports

**What You Handle:**
- React admin interface development and deployment
- UI/UX improvements and new features
- Form validation and user experience
- Admin-specific functionality and workflows

### 🎯 Success Metrics

**Phase 1 (Current):**
- [ ] Real database connection working
- [ ] Basic CRUD operations functional
- [ ] Forms properly validate data
- [ ] Deployment pipeline established

**Phase 2 (Future):**
- [ ] Bulk operations implemented
- [ ] Advanced search and filtering
- [ ] Export/import capabilities
- [ ] Performance optimization

**Phase 3 (Polish):**
- [ ] User feedback integration
- [ ] Advanced admin workflows
- [ ] Monitoring and analytics
- [ ] Documentation for end users

Welcome to the team! The foundation is solid, and we're excited to see what you build on top of it. 🌺