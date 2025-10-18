# Edit Short URL Feature - Testing Guide

## Quick Test Steps

### Setup
1. Ensure both backend and frontend are running:
   - Backend: `docker-compose -f local.yml up`
   - Frontend: `cd frontend && npm run dev`
2. Login as a user who is an **Admin** or **Editor** of an organization

### Test Scenario 1: Edit Existing URL (Admin/Editor)

1. **Navigate to URLs page:**
   - Go to http://localhost:5173/urls

2. **Create a test URL (if needed):**
   - Click "Create Short URL"
   - Select a namespace
   - Enter original URL: `https://example.com`
   - Leave short code empty (auto-generate)
   - Click "Create"

3. **Edit the URL:**
   - Find the URL in the list
   - Click the green "Edit" button
   - Modal should open with pre-filled data
   - Modal title should show "Edit Short URL"

4. **Make changes:**
   - Change original URL to `https://updated-example.com`
   - Change tags to `updated, test`
   - Toggle "Private URL" checkbox
   - Click "Update"

5. **Verify:**
   - Modal should close
   - URL list should refresh automatically
   - Updated values should be visible in the list
   - Click count should remain unchanged

### Test Scenario 2: Edit Short Code

1. **Edit a URL:**
   - Click "Edit" on any URL
   - Change the short code to something unique: `my-custom-edit-code`
   - Click "Update"

2. **Verify:**
   - URL should update successfully
   - Full short URL should reflect the new short code
   - Old short code should no longer work

3. **Test duplicate short code:**
   - Edit another URL in the same namespace
   - Try to use the same short code: `my-custom-edit-code`
   - Should show error: "This short code is already taken in this namespace."

### Test Scenario 3: Permission Validation

1. **As a Viewer:**
   - Login as a user with **Viewer** role
   - Navigate to URLs page
   - Edit button should still appear (frontend doesn't restrict)
   - Click "Edit" on a URL
   - Make changes and click "Update"
   - Should receive error: "Only organization admins and editors can update short URLs."

2. **As non-member:**
   - Try to directly call API: `PATCH /api/short-urls/{id}/`
   - Should receive permission denied error

### Test Scenario 4: Field Validation

1. **Test required fields:**
   - Edit a URL
   - Clear the "Original URL" field
   - Click "Update"
   - Should show validation error

2. **Test URL format:**
   - Edit a URL
   - Enter invalid URL: `not-a-valid-url`
   - Should show validation error

3. **Test empty short code:**
   - Edit a URL
   - Clear the short code field
   - Click "Update"
   - Should update successfully (auto-generates new code)

### Test Scenario 5: Namespace Change

1. **Edit a URL:**
   - Click "Edit"
   - Change the namespace dropdown to a different namespace (in same org)
   - Click "Update"

2. **Verify:**
   - URL should move to the new namespace
   - Full short URL should reflect the new namespace
   - Short code uniqueness is checked in the new namespace

### Test Scenario 6: Cancel Edit

1. **Edit a URL:**
   - Click "Edit" on any URL
   - Make some changes to the form
   - Click "Cancel"

2. **Verify:**
   - Modal should close
   - No changes should be saved
   - Create a new URL to verify create still works

3. **Edit again:**
   - Click "Edit" on the same URL
   - Form should show original (unchanged) values

## Expected Behavior Summary

### ✅ Success Cases:
- Admin can edit short URLs
- Editor can edit short URLs
- All fields can be updated
- Short code can be changed to unique value
- Namespace can be changed within same organization
- Empty short code auto-generates new code
- Form pre-fills with existing data
- Modal title changes based on mode
- Button text changes (Create/Update)
- List refreshes after update

### ❌ Error Cases:
- Viewer cannot edit (403 Forbidden)
- Non-member cannot edit (403 Forbidden)
- Duplicate short code in same namespace (400 Bad Request)
- Invalid URL format (400 Bad Request)
- Empty required fields (400 Bad Request)

## API Testing with curl

### Update a Short URL:
```bash
# Get auth token first
curl -X POST http://localhost:8000/rest-auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Update short URL (replace {id} and {token})
curl -X PATCH http://localhost:8000/api/short-urls/{id}/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "namespace_id": 1,
    "original_url": "https://updated-example.com",
    "short_code": "updated-code",
    "tags": "updated, tags",
    "is_private": true
  }'
```

### Expected Response:
```json
{
  "id": 1,
  "namespace": {
    "id": 1,
    "name": "default",
    "organization": {...}
  },
  "short_code": "updated-code",
  "original_url": "https://updated-example.com",
  "full_short_url": "http://localhost:8000/default/updated-code/",
  "tags": "updated, tags",
  "tags_list": ["updated", "tags"],
  "is_private": true,
  "created_by": {...},
  "created_at": "2025-10-18T...",
  "updated_at": "2025-10-18T...",
  "click_count": 5,
  "is_expired": false
}
```

## Common Issues & Solutions

### Issue: "short_code: This field is required" when clearing short code
**Solution:** This is now fixed - empty short code auto-generates a new one

### Issue: Edit button doesn't appear
**Solution:** Check that you're logged in and viewing URLs page

### Issue: Permission denied error
**Solution:** Verify user is Admin or Editor of the organization

### Issue: Modal doesn't pre-fill data
**Solution:** Check browser console for errors, verify API returns full URL object

### Issue: Changes not visible after update
**Solution:** React Query should auto-refresh, check network tab to verify API call succeeded

## Browser DevTools Debugging

### Check Network Tab:
1. Open DevTools (F12)
2. Go to Network tab
3. Click "Edit" button
4. Make changes and click "Update"
5. Look for PATCH request to `/api/short-urls/{id}/`
6. Check status code (should be 200)
7. Check response body for updated data

### Check Console:
- Any JavaScript errors?
- React Query mutation logs?
- API client logs?

## Database Verification

### Check in Django Admin:
1. Go to http://localhost:8000/admin/
2. Navigate to URL Shortener > Short URLs
3. Find the edited URL
4. Verify changes are saved in database
5. Check `updated_at` timestamp is recent

### Check with Django Shell:
```bash
docker-compose -f local.yml run --rm django python manage.py shell
```

```python
from hirethon_template.url_shortener.models import ShortURL
url = ShortURL.objects.get(id=1)
print(f"Short Code: {url.short_code}")
print(f"Original URL: {url.original_url}")
print(f"Updated At: {url.updated_at}")
```

