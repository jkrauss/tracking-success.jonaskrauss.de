import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function LoginPage() {
  const { login, register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [info, setInfo] = useState('');
  const [showResend, setShowResend] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');
    setShowResend(false);
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password);
        setInfo('You will receive a confirmation email shortly. Click the link inside to log in.');
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      const statusCode = err.message?.match(/(\d{3})/)?.[1];
      if (statusCode === '403') {
        setError('Email not confirmed. Please check your inbox.');
        setShowResend(true);
      } else {
        setError(err.message || 'Authentifizierung fehlgeschlagen');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email) {
      setError('Bitte gib zuerst deine E-Mail-Adresse ein.');
      return;
    }
    setError('');
    setInfo('');
    setLoading(true);
    try {
      await api.auth.forgotPassword(email);
      setInfo('If the email address exists, a reset link has been sent.');
    } catch (err: any) {
      if (err.message?.includes('not found')) {
        setError('Diese E-Mail-Adresse ist nicht registriert.');
      } else {
        setError(err.message || 'Anfrage fehlgeschlagen');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendConfirmation = async () => {
    if (!email) return;
    setError('');
    setInfo('');
    setLoading(true);
    try {
      await api.auth.resendConfirmation(email);
      setInfo('Confirmation email has been resent. Please check your inbox.');
      setShowResend(false);
    } catch (err: any) {
      setError(err.message || 'Erneutes Senden fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[100dvh] flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl text-center">
            {isRegister ? 'Create account' : 'Sign in'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {info && <p className="text-sm text-green-600 mb-3">{info}</p>}
          <form onSubmit={handleSubmit} className="space-y-3">
            <Input
              type="email"
              placeholder="E-Mail"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-10"
              required
            />
            <Input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-10"
              required
            />
            {error && <p className="text-destructive text-xs">{error}</p>}
            {showResend && (
              <button
                type="button"
                className="w-full text-xs text-primary hover:underline"
                onClick={handleResendConfirmation}
                disabled={loading}
              >
                Resend confirmation email
              </button>
            )}
            <Button type="submit" className="w-full h-10" disabled={loading}>
              {loading ? '...' : isRegister ? 'Register' : 'Sign in'}
            </Button>
            {!isRegister && (
              <button
                type="button"
                className="w-full text-xs text-muted-foreground hover:text-primary"
                onClick={handleForgotPassword}
                disabled={loading}
              >
                Forgot password?
              </button>
            )}
            <Button
              type="button"
              variant="ghost"
              className="w-full h-9 text-sm"
              onClick={() => {
                setIsRegister(!isRegister);
                setError('');
                setInfo('');
                setShowResend(false);
              }}
            >
              {isRegister ? 'Already have an account? Sign in' : 'Create new account'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}