import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get('token');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="h-[100dvh] flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-xl text-center">Passwort zurücksetzen</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center text-sm text-destructive">Kein Token gefunden.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 6) {
      setError('Passwort muss mindestens 6 Zeichen lang sein.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwörter stimmen nicht überein.');
      return;
    }

    setLoading(true);
    try {
      await api.auth.resetPasswordConfirm(token, newPassword);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Zurücksetzen fehlgeschlagen.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-[100dvh] flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl text-center">Passwort zurücksetzen</CardTitle>
        </CardHeader>
        <CardContent>
          {success ? (
            <div className="space-y-4">
              <p className="text-center text-sm text-green-600">
                Dein Passwort wurde zurückgesetzt. Du kannst dich jetzt anmelden.
              </p>
              <button
                className="w-full text-sm text-primary hover:underline"
                onClick={() => navigate('/login')}
              >
                Zur Anmeldung →
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <Input
                type="password"
                placeholder="Neues Passwort"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="h-10"
                required
              />
              <Input
                type="password"
                placeholder="Passwort wiederholen"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="h-10"
                required
              />
              {error && <p className="text-destructive text-xs">{error}</p>}
              <Button type="submit" className="w-full h-10" disabled={loading}>
                {loading ? '...' : 'Passwort zurücksetzen'}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}