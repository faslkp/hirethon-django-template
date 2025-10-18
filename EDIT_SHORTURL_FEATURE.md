# Edit Short URL Feature for Admins and Editors

## Overview
Implemented a comprehensive edit feature for short URLs that allows organization admins and editors to modify existing short URLs.

## Backend Changes

### 1. Added `perform_update` Method to `ShortURLViewSet`
**File:** `hirethon_template/url_shortener/api/views.py`

```python
def perform_update(self, serializer):
    """Override perform_update to validate permissions"""
    # Get the namespace - either from the new data or from the existing object
    namespace = serializer.validated_data.get('namespace', self.get_object().namespace)
    organization = namespace.organization
    
    # Verify user is editor or admin
    is_editor_or_admin = OrganizationMembership.objects.filter(
        organization=organization,
        user=self.request.user,
        role__in=[OrganizationMembership.Role.ADMIN, OrganizationMembership.Role.EDITOR]
    ).exists()
    
    if not is_editor_or_admin:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Only organization admins and editors can update short URLs.")
    
    serializer.save()
```

**Key Features:**
- Validates that only admins and editors can update short URLs
- Checks permissions against the organization of the short URL's namespace
- Raises `PermissionDenied` if user doesn't have proper role

### 2. Existing Permission Classes
The viewset already had:
- `CanManageShortURL` permission class (allows admins and editors)
- Proper permissions configured for 'update' and 'partial_update' actions
- Serializer with proper validation for uniqueness during updates

## Frontend Changes

### 1. Updated `URLs.jsx` Component
**File:** `frontend/src/pages/URLs.jsx`

#### Added State Management:
```javascript
const [editingUrl, setEditingUrl] = useState(null);
const updateUrl = useUpdateShortUrl();
```

#### Unified Submit Handler:
```javascript
const handleSubmit = async (e) => {
  // Handles both create and update operations
  if (editingUrl) {
    await updateUrl.mutateAsync({ id: editingUrl.id, data });
  } else {
    await createUrl.mutateAsync(data);
  }
}
```

#### New Edit Handler:
```javascript
const handleEdit = (url) => {
  setEditingUrl(url);
  setFormData({
    namespace_id: url.namespace.id,
    original_url: url.original_url,
    short_code: url.short_code,
    tags: url.tags || '',
    is_private: url.is_private,
  });
  setShowModal(true);
};
```

#### Enhanced Modal Close Handler:
```javascript
const handleCloseModal = () => {
  setShowModal(false);
  setEditingUrl(null);
  setFormData({ namespace_id: '', original_url: '', short_code: '', tags: '', is_private: false });
  setFormErrors({});
};
```

### 2. Updated UI Components

#### Added Edit Button in Actions Column:
```javascript
<button
  onClick={() => handleEdit(url)}
  className="text-green-600 hover:text-green-800"
  title="Edit"
>
  Edit
</button>
```

#### Dynamic Modal Title:
```javascript
<h2 className="text-xl font-bold mb-4">
  {editingUrl ? 'Edit Short URL' : 'Create Short URL'}
</h2>
```

#### Dynamic Submit Button:
```javascript
<button
  type="submit"
  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
  disabled={editingUrl ? updateUrl.isPending : createUrl.isPending}
>
  {editingUrl 
    ? (updateUrl.isPending ? 'Updating...' : 'Update')
    : (createUrl.isPending ? 'Creating...' : 'Create')
  }
</button>
```

## Existing Infrastructure Used

### 1. React Query Hook
**File:** `frontend/src/hooks/useShortUrls.js`

The `useUpdateShortUrl` hook already existed:
```javascript
export const useUpdateShortUrl = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => shortUrlsAPI.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['short-urls'] });
    },
  });
};
```

### 2. API Client Method
**File:** `frontend/src/api/shortUrls.js`

The API client already had the update method:
```javascript
update: (id, data) => apiClient.patch(`/short-urls/${id}/`, data),
```

### 3. Serializer Validation
**File:** `hirethon_template/url_shortener/api/serializers.py`

The `ShortURLSerializer` already handled updates properly:
- Excludes current instance from uniqueness checks during updates
- Properly validates all fields
- Handles optional short_code field

## Features

### 1. Role-Based Access Control
- Only admins and editors can edit short URLs
- Backend validates permissions on every update request
- Frontend shows edit button to all users (backend enforces actual permissions)

### 2. Field Editing
Users can edit:
- **Namespace** - Change which namespace the URL belongs to
- **Original URL** - Update the destination URL
- **Short Code** - Modify the short code (with uniqueness validation)
- **Tags** - Update comma-separated tags
- **Privacy** - Toggle private/public status

### 3. Validation
- Short code uniqueness within namespace (excluding current URL)
- Required field validation
- URL format validation
- Permission validation

### 4. User Experience
- Single modal for both create and edit operations
- Pre-filled form when editing
- Dynamic button states (Creating/Updating)
- Error handling and display
- Loading states during API calls

## Testing Checklist

### Backend Tests:
- [ ] Admin can update short URLs in their organization
- [ ] Editor can update short URLs in their organization
- [ ] Viewer cannot update short URLs (permission denied)
- [ ] Cannot update short URL to duplicate short_code in same namespace
- [ ] Can update short URL to existing short_code in different namespace
- [ ] Cannot update short URL in organization user is not a member of

### Frontend Tests:
- [ ] Edit button appears in URL list
- [ ] Clicking edit opens modal with pre-filled data
- [ ] Modal title shows "Edit Short URL"
- [ ] Submit button shows "Update" / "Updating..."
- [ ] Successfully updates URL and refreshes list
- [ ] Shows validation errors from backend
- [ ] Cancel button clears edit state
- [ ] Creating new URL still works as before

## API Endpoints Used

### Update Short URL
```
PATCH /api/short-urls/{id}/
```

**Request Body:**
```json
{
  "namespace_id": 1,
  "original_url": "https://updated-example.com",
  "short_code": "updated-code",
  "tags": "new, tags",
  "is_private": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "namespace": {...},
  "short_code": "updated-code",
  "original_url": "https://updated-example.com",
  "full_short_url": "http://localhost:8000/namespace/updated-code/",
  "tags": "new, tags",
  "is_private": true,
  "created_by": {...},
  "created_at": "2025-10-18T...",
  "updated_at": "2025-10-18T...",
  "click_count": 5
}
```

**Error Response (403 Forbidden):**
```json
{
  "detail": "Only organization admins and editors can update short URLs."
}
```

**Error Response (400 Bad Request):**
```json
{
  "short_code": ["This short code is already taken in this namespace."]
}
```

## Security Considerations

1. **Permission Validation:** Double-checked at both permission class and perform_update levels
2. **Organization Isolation:** Users can only edit URLs in organizations they're members of
3. **Role Enforcement:** Only admins and editors have edit access
4. **Data Validation:** All fields validated before saving

## Future Enhancements

1. **Bulk Edit:** Allow editing multiple URLs at once
2. **Edit History:** Track changes made to short URLs
3. **Conditional Edit:** Only allow editing if URL hasn't been used (click_count == 0)
4. **Field-Level Permissions:** Different fields editable by different roles
5. **Audit Log:** Log who made what changes and when

