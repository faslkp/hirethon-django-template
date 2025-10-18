import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { useGetInvitation, useAcceptInvitation } from '../hooks/useInvitations';
import { useAuthStore } from '../store/authStore';

export const AcceptInvite = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  const { user } = useAuthStore();
  
  const { data: invitation, isLoading, error } = useGetInvitation(token);
  const acceptInvitation = useAcceptInvitation();
  
  const [accepting, setAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    // If user is logged in and invitation is valid, show accept button
    // If user is not logged in, redirect to register with token
    if (!token) {
      navigate('/login');
    }
  }, [token, navigate]);

  const handleAccept = async () => {
    try {
      setAccepting(true);
      await acceptInvitation.mutateAsync(token);
      setAccepted(true);
      
      // Redirect to organization page after 2 seconds
      setTimeout(() => {
        navigate('/organizations');
      }, 2000);
    } catch (err) {
      console.error('Failed to accept invitation:', err);
      setAccepting(false);
    }
  };

  if (!token) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid Invitation</h1>
            <p className="text-gray-600 mb-6">No invitation token provided.</p>
            <Link to="/login" className="text-blue-600 hover:underline">
              Go to Login
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading invitation...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md">
            <div className="text-red-600 text-5xl mb-4">✗</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Invalid or Expired Invitation</h1>
            <p className="text-gray-600 mb-6">
              {error.response?.data?.error || 'This invitation is no longer valid.'}
            </p>
            <Link to="/login" className="text-blue-600 hover:underline">
              Go to Login
            </Link>
          </div>
        </div>
      </Layout>
    );
  }

  if (accepted) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center max-w-md">
            <div className="text-green-600 text-5xl mb-4">✓</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Invitation Accepted!</h1>
            <p className="text-gray-600 mb-6">
              You've joined {invitation?.organization?.name}. Redirecting...
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  // If user is not logged in, redirect to register with token
  if (!user && invitation) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="bg-white shadow rounded-lg p-8 max-w-md w-full">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">You're Invited!</h1>
              <p className="text-gray-600">
                {invitation.invited_by?.name || invitation.invited_by?.email} has invited you to join
              </p>
              <h2 className="text-xl font-semibold text-blue-600 mt-2">
                {invitation.organization?.name}
              </h2>
              <p className="text-sm text-gray-500 mt-2">
                as a <span className="font-semibold">{invitation.role}</span>
              </p>
            </div>

            <div className="space-y-4">
              <Link
                to={`/register?invite=${token}`}
                className="block w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-center"
              >
                Create Account & Accept
              </Link>
              <Link
                to={`/login?invite=${token}`}
                className="block w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 text-center"
              >
                Already have an account? Sign In
              </Link>
            </div>

            <p className="text-xs text-gray-500 mt-6 text-center">
              This invitation expires on {new Date(invitation.expires_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  // User is logged in, show accept button
  return (
    <Layout>
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-white shadow rounded-lg p-8 max-w-md w-full">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">You're Invited!</h1>
            <p className="text-gray-600">
              {invitation.invited_by?.name || invitation.invited_by?.email} has invited you to join
            </p>
            <h2 className="text-xl font-semibold text-blue-600 mt-2">
              {invitation.organization?.name}
            </h2>
            <p className="text-sm text-gray-500 mt-2">
              as a <span className="font-semibold">{invitation.role}</span>
            </p>
          </div>

          <div className="space-y-4">
            <button
              onClick={handleAccept}
              disabled={accepting}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {accepting ? 'Accepting...' : 'Accept Invitation'}
            </button>
            <Link
              to="/organizations"
              className="block w-full bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200 text-center"
            >
              Cancel
            </Link>
          </div>

          <p className="text-xs text-gray-500 mt-6 text-center">
            This invitation expires on {new Date(invitation.expires_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </Layout>
  );
};

