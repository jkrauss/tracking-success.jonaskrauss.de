import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
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
            <Button type="submit" className="w-full h-10" disabled={loading}>
              {loading ? '...' : isRegister ? 'Registrieren' : 'Anmelden'}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="w-full h-9 text-sm"
              onClick={() => setIsRegister(!isRegister)}
            >
              {isRegister ? 'Bereits ein Konto? Anmelden' : 'Neues Konto erstellen'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
