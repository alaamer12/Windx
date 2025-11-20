# Admin Dashboard Documentation

## Overview

The Admin Dashboard is a comprehensive web interface for managing and monitoring the application. It provides real-time statistics, data entry forms, and administrative tools.

## Features

### ✨ Key Features

- **Real-time Statistics** - Live dashboard with auto-updating metrics
- **Data Entry Forms** - Comprehensive forms with validation
- **Image Upload** - Drag-and-drop image handling
- **Form Validation** - Client-side validation with error messages
- **Draft Saving** - Save form progress locally
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Modern UI** - Built with Tailwind CSS and Alpine.js
- **Toast Notifications** - User-friendly feedback messages

## Access

### URL
```
http://localhost:8000/api/v1/dashboard/
```

### Requirements
- Must be logged in as **superuser**
- Valid JWT token required
- Admin privileges

## Dashboard Pages

### 1. Main Dashboard (`/api/v1/dashboard/`)

**Features**:
- Total users count
- Active users count
- New users today
- New users this week
- Recent users table
- Quick action buttons

**Statistics Cards**:
- **Total Users** - Blue card with total count
- **Active Users** - Green card with active percentage
- **New Today** - Purple card with today's registrations

**Quick Actions**:
- Add New Data
- Export Data (CSV/JSON)
- View API Documentation

### 2. Data Entry Form (`/api/v1/dashboard/data-entry`)

**Form Sections**:

#### Basic Information
- **Username** (required)
  - 3-50 characters
  - Letters, numbers, underscores only
  - Real-time validation
  
- **Email** (required)
  - Valid email format
  - Unique constraint
  
- **Full Name** (optional)
  - Up to 100 characters
  
- **Password** (required)
  - Minimum 8 characters
  - Show/hide toggle

#### Status & Permissions
- **Active Account** - Checkbox to enable/disable user
- **Superuser** - Checkbox to grant admin privileges

#### Profile Image
- **Image Upload**
  - Drag and drop support
  - File picker
  - Preview before upload
  - Remove uploaded image
  - Max size: 10MB
  - Formats: PNG, JPG, GIF

#### Additional Information
- **Join Date** - Date picker
- **Role** - Dropdown (User, Moderator, Admin)
- **Age** - Number input (18-120)
- **Website** - URL input
- **Biography** - Textarea (500 characters max)

**Form Actions**:
- **Reset Form** - Clear all fields
- **Save Draft** - Save to localStorage
- **Submit** - Create new user

## Technical Stack

### Frontend
- **Tailwind CSS** - Utility-first CSS framework
- **Alpine.js** - Lightweight JavaScript framework
- **Font Awesome** - Icon library
- **Jinja2** - Template engine

### Backend
- **FastAPI** - Python web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation

## Features in Detail

### Real-time Updates

Dashboard statistics auto-refresh every 30 seconds:

```javascript
// Auto-refresh stats every 30 seconds
setInterval(() => {
    fetch('/api/v1/dashboard/stats')
        .then(res => res.json())
        .then(data => {
            // Update stats
        });
}, 30000);
```

### Form Validation

Client-side validation with instant feedback:

```javascript
validateField(field) {
    if (field === 'username') {
        if (this.formData.username.length < 3) {
            this.errors.username = 'Username must be at least 3 characters';
        }
    }
}
```

### Image Upload

Drag-and-drop with preview:

```javascript
handleImageUpload(event) {
    const file = event.target.files[0];
    if (file.size > 10 * 1024 * 1024) {
        showToast('Image size must be less than 10MB', 'error');
        return;
    }
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        this.imagePreview = e.target.result;
    };
    reader.readAsDataURL(file);
}
```

### Draft Saving

Forms automatically save to localStorage:

```javascript
saveAsDraft() {
    localStorage.setItem('formDraft', JSON.stringify(this.formData));
    showToast('Draft saved successfully', 'success');
}
```

## API Endpoints

### Get Dashboard
```http
GET /api/v1/dashboard/
Authorization: Bearer {token}
```

**Response**: HTML page

### Get Statistics
```http
GET /api/v1/dashboard/stats
Authorization: Bearer {token}
```

**Response**:
```json
{
  "total_users": 100,
  "active_users": 95,
  "inactive_users": 5,
  "superusers": 2,
  "new_users_today": 3,
  "new_users_week": 15,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Get Data Entry Form
```http
GET /api/v1/dashboard/data-entry
Authorization: Bearer {token}
```

**Response**: HTML form

## Styling Guide

### Color Scheme

- **Primary**: Blue (#2563EB)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#EF4444)
- **Info**: Purple (#8B5CF6)

### Components

#### Stat Card
```html
<div class="stat-card">
    <div class="flex items-center justify-between">
        <div>
            <p class="text-blue-100 text-sm font-medium">Label</p>
            <p class="text-4xl font-bold mt-2">Value</p>
        </div>
        <div class="bg-white bg-opacity-20 rounded-full p-4">
            <i class="fas fa-icon text-3xl"></i>
        </div>
    </div>
</div>
```

#### Input Field
```html
<div>
    <label class="label" for="field">
        Label <span class="text-red-500">*</span>
    </label>
    <input 
        type="text" 
        id="field" 
        class="input-field"
        placeholder="Enter value"
    >
</div>
```

#### Button
```html
<button class="btn-primary">
    <i class="fas fa-check mr-2"></i>
    Submit
</button>
```

## Customization

### Adding New Fields

1. **Add to HTML template**:
```html
<div>
    <label class="label" for="new_field">
        New Field
    </label>
    <input 
        type="text" 
        id="new_field" 
        x-model="formData.new_field"
        class="input-field"
    >
</div>
```

2. **Add to Alpine.js data**:
```javascript
formData: {
    // ... existing fields
    new_field: ''
}
```

3. **Add validation** (if needed):
```javascript
validateField(field) {
    if (field === 'new_field') {
        // Validation logic
    }
}
```

### Adding New Statistics

1. **Update backend**:
```python
stats = {
    # ... existing stats
    "new_stat": calculate_new_stat()
}
```

2. **Add to template**:
```html
<div class="stat-card">
    <p id="stat-new_stat">{{ stats.new_stat }}</p>
</div>
```

## Best Practices

### Security
- ✅ Always require superuser authentication
- ✅ Validate all inputs server-side
- ✅ Sanitize user input
- ✅ Use CSRF protection
- ✅ Implement rate limiting

### Performance
- ✅ Cache static assets
- ✅ Lazy load images
- ✅ Debounce form validation
- ✅ Use pagination for large lists
- ✅ Minimize API calls

### UX
- ✅ Provide instant feedback
- ✅ Show loading states
- ✅ Display error messages clearly
- ✅ Save form progress
- ✅ Confirm destructive actions

## Troubleshooting

### Issue: Dashboard not loading

**Solution**: Check authentication
```bash
# Verify token is valid
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/auth/me
```

### Issue: Form submission fails

**Solution**: Check browser console for errors
```javascript
// Open browser console (F12)
// Look for error messages
```

### Issue: Images not uploading

**Solution**: Check file size and format
```javascript
// Max size: 10MB
// Formats: PNG, JPG, GIF
```

### Issue: Stats not updating

**Solution**: Check auto-refresh is working
```javascript
// Should refresh every 30 seconds
// Check browser console for errors
```

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Mobile Support

- ✅ Responsive design
- ✅ Touch-friendly buttons
- ✅ Mobile-optimized forms
- ✅ Swipe gestures

## Future Enhancements

- [ ] Bulk data import (CSV/Excel)
- [ ] Advanced filtering and search
- [ ] Data visualization charts
- [ ] Export to PDF
- [ ] Email notifications
- [ ] Audit logs
- [ ] User activity tracking
- [ ] Dark mode

## References

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Font Awesome Icons](https://fontawesome.com/icons)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
