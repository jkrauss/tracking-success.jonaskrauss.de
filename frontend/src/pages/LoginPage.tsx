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
        setInfo('Bestätigungs-E-Mail wurde gesendet. Bitte überprüfe dein Postfach und klicke auf den Link, um dein Konto zu aktivieren.');
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(err.message || 'Authentifizierung fehlgeschlagen');
      if (err.message && err.message.includes('nicht bestätigt')) {
        setShowResend(true);
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
      setInfo('Wenn die E-Mail-Adresse existiert, wurde ein Link zum Zurücksetzen gesendet.');
    } catch (err: any) {
      if (err.message && err.message.includes('not found')) {
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
      setInfo('Bestätigungs-E-Mail wurde erneut gesendet. Bitte überprüfe dein Postfach.');
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
            {isRegister ? 'Konto erstellen' : 'Anmelden'}
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
              placeholder="Passwort"
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
                Bestätigungs-E-Mail erneut senden
              </button>
            )}
            <Button type="submit" className="w-full h-10" disabled={loading}>
              {loading ? '...' : isRegister ? 'Registrieren' : 'Anmelden'}
            </Button>
            {!isRegister && (
              <button
                type="button"
                className="w-full text-xs text-muted-foreground hover:text-primary"
                onClick={handleForgotPassword}
                disabled={loading}
              >
                Passwort vergessen?
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
              {isRegister ? 'Bereits ein Konto? Anmelden' : 'Neues Konto erstellen'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}