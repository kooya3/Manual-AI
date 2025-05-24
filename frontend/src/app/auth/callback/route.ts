import { createClient } from '@/lib/supabase/server';
import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  // The `/auth/callback` route is required for the server-side auth flow implemented
  // by the SSR package. It exchanges an auth code for the user's session.
  // https://supabase.com/docs/guides/auth/server-side/nextjs
  console.log('Auth callback route hit.');
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get('code');
  const returnUrl = requestUrl.searchParams.get('returnUrl');
  const origin = requestUrl.origin;

  console.log('Auth code:', code);
  console.log('Return URL:', returnUrl);

  if (code) {
    const supabase = await createClient();
    const { data, error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      console.error('Error exchanging code for session:', error.message);
      // Optionally, redirect to an error page or add error handling
      return NextResponse.redirect(`${origin}/auth?error=${encodeURIComponent(error.message)}`);
    }
    console.log('Successfully exchanged code for session. User:', data.user?.id);
  }

  // URL to redirect to after sign up process completes
  // Handle the case where returnUrl is 'null' (string) or actual null
  const redirectPath =
    returnUrl && returnUrl !== 'null' ? returnUrl : '/dashboard';
  // Make sure to include a slash between origin and path if needed
  const finalRedirectUrl = `${origin}${redirectPath.startsWith('/') ? '' : '/'}${redirectPath}`;
  console.log('Redirecting to:', finalRedirectUrl);

  return NextResponse.redirect(finalRedirectUrl);
}
