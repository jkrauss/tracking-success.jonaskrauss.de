import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export function ConfirmEmailPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = params.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Kein Token gefunden.');
      return;
    }
    api.auth
      .confirmEmail(token)
      .then(() => {
        setStatus('success');
        setMessage('Your email has been confirmed. You can now sign in.');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.message || 'Confirmation failed.');
      });
  }, [params]);

  return (
    <div className="h-[100dvh] flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-xl text-center">Confirm email</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {status === 'loading' && (
            <p className="text-center text-sm text-muted-foreground">Confirming…</p>
          )}
          {status === 'success' && (
            <>
              <p className="text-center text-sm text-green-600">{message}</p>
              <button
                className="w-full text-sm text-primary hover:underline"
                onClick={() => navigate('/login')}
              >
                Go to sign in →
              </button>
            </>
          )}
          {status === 'error' && (
            <p className="text-center text-sm text-destructive">{message}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}