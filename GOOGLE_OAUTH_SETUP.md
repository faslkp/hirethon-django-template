# Google OAuth Setup Guide (Simplified)

This guide explains how to set up Google OAuth authentication using **React OAuth only** - no complex django-allauth redirects needed!

## Frontend Configuration (React OAuth)

### 1. Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Google OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your-google-client-id-here
```

### 2. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" in the left sidebar
5. Click "Create Credentials" > "OAuth 2.0 Client IDs"
6. Choose "Web application" as the application type
7. **Important**: Add authorized JavaScript origins (NOT redirect URIs):
   - For development: `http://localhost:5173`
   - For production: `https://yourdomain.com`
8. Copy the Client ID (you don't need the secret for React OAuth)

## How It Works (Simplified)

### 1. **React Frontend**
- User clicks "Continue with Google" button
- React opens Google OAuth popup
- User authenticates with Google
- React gets Google access token
- React sends token to Django backend

### 2. **Django Backend**
- Receives Google access token from React
- Verifies token with Google API
- Creates/updates user account
- Returns JWT tokens to React
- React stores JWT and user is logged in

## Features Implemented

### Backend Features
- ✅ Simple Google token verification endpoint at `/api/auth/google/`
- ✅ Automatic user creation from Google profile
- ✅ JWT token generation
- ✅ No complex django-allauth redirects needed

### Frontend Features
- ✅ Google OAuth provider wrapper in React app
- ✅ Google login button component with popup flow
- ✅ Integration with existing auth store
- ✅ Google login buttons on Login and Register pages
- ✅ Support for invitation flow with Google login

## Usage

### For Users
1. Visit the Login or Register page
2. Click "Continue with Google" button
3. Complete Google OAuth flow in popup
4. User is automatically logged in and redirected

### For Developers
The Google login button automatically:
- Opens Google OAuth popup
- Handles the OAuth flow
- Sends the access token to the backend
- Stores JWT tokens in localStorage
- Redirects based on invitation tokens or next URLs

## Testing

1. **Set up Google OAuth credentials** in Google Cloud Console
2. **Add environment variables** to `frontend/.env`:
   ```bash
   VITE_GOOGLE_CLIENT_ID=your-google-client-id-here
   VITE_API_URL=http://localhost:8000
   ```
3. **Start the Django backend**: `python manage.py runserver`
4. **Start the React frontend**: `cd frontend && npm run dev`
5. **Visit** `http://localhost:5173/login` or `http://localhost:5173/register`
6. **Click "Continue with Google"** to test the flow

## Troubleshooting

### Common Issues

1. **"Invalid client" error**: Check that your Google Client ID is correct in the frontend `.env` file.

2. **CORS errors**: Ensure your frontend URL (`http://localhost:5173`) is added to the Google OAuth authorized JavaScript origins in Google Cloud Console.

3. **"Access blocked" error**: Make sure you're using **JavaScript origins** (not redirect URIs) in Google Cloud Console.

4. **Frontend not loading**: Check that `VITE_GOOGLE_CLIENT_ID` is set in your frontend `.env` file.

### Debug Steps

1. Check browser console for JavaScript errors
2. Check Django logs for backend errors  
3. Verify environment variables are loaded correctly
4. Test the Google OAuth flow in Google Cloud Console's OAuth 2.0 Playground

## Key Differences from Complex Setup

- ✅ **No redirect URIs needed** - React handles OAuth in popup
- ✅ **No django-allauth configuration** - Simple token verification
- ✅ **No Google Client Secret needed** - React OAuth doesn't require it
- ✅ **No redirect_uri_mismatch errors** - No server-side redirects
