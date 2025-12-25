# Peacock Server Refactoring Plan

## Current State
- `peacock_server.py`: 1203 lines (monolithic)
- Inline CSS, JavaScript, and HTML
- All logic in global scope with minimal structure

## Target Structure

```
Peacock/
├── static/
│   ├── style.css      ✅ Created (395 lines)
│   └── app.js         ✅ Created (372 lines)
├── templates/
│   └── index.html     ⏳ To create
├── lib/
│   ├── __init__.py
│   ├── metadata_manager.py
│   └── title_suggester.py
└── peacock_server.py  ⏳ To refactor (~200 lines)
```

## Benefits
1. **Maintainability**: Separate concerns (CSS/JS/Python)
2. **Readability**: Class-based structure with clear responsibilities
3. **Testability**: Modular components can be unit tested
4. **Scalability**: Easy to add features without bloating main file

## Implementation Phases

### Phase 1: Static Assets ✅ DONE
- [x] Extract CSS to `static/style.css`
- [x] Extract JavaScript to `static/app.js`

### Phase 2: HTML Template (Next)
- [ ] Create Jinja2 template in `templates/index.html`
- [ ] Use template variables for config
- [ ] Serve static files through Flask

### Phase 3: Python Refactoring
- [ ] Create `lib/metadata_manager.py` class
- [ ] Create `lib/title_suggester.py` class
- [ ] Refactor `peacock_server.py` to use classes
- [ ] Use Flask blueprints for better route organization

### Phase 4: Configuration
- [ ] Move configuration to class
- [ ] Environment-based settings
- [ ] Better error handling

## Next Steps
1. Create HTML template
2. Refactor Python code with classes
3. Update .gitignore for lib/__pycache__
4. Test all functionality
5. Update README with new structure
