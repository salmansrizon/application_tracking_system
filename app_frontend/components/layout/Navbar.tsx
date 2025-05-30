'use client';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

const Navbar = () => {
  const { isAuthenticated, user, logout, isLoading } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (isLoading) {
    // Optional: render a slim loading state or null for navbar during initial load
    return (
      <nav className="bg-gray-800 text-white p-4">
        <div className="container mx-auto flex justify-between items-center">
          <Link href="/" className="text-xl font-bold">AppTracker</Link>
          <div>Loading...</div>
        </div>
      </nav>
    );
  }

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link href={isAuthenticated ? "/dashboard" : "/"} className="text-xl font-bold">
          AppTracker
        </Link>
        <div>
          {isAuthenticated ? (
            <>
              <span className="mr-4">Welcome, {user?.email}</span>
              <Link href="/jobs" className="mr-4 hover:text-gray-300">My Jobs</Link>
              <button onClick={handleLogout} className="hover:text-gray-300">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="mr-4 hover:text-gray-300">
                Login
              </Link>
              <Link href="/register" className="hover:text-gray-300">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
