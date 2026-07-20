import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginForm } from './LoginForm';

describe('LoginForm', () => {
  it('submits the entered credentials', async () => {
    const onLogin = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<LoginForm onLogin={onLogin} />);

    await user.type(screen.getByLabelText(/username/i), 'jeanine');
    await user.type(screen.getByLabelText(/password/i), 'correct-horse');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(onLogin).toHaveBeenCalledWith('jeanine', 'correct-horse');
  });

  it('shows an error message when login fails', async () => {
    const onLogin = vi.fn().mockRejectedValue(new Error('nope'));
    const user = userEvent.setup();
    render(<LoginForm onLogin={onLogin} />);

    await user.type(screen.getByLabelText(/username/i), 'jeanine');
    await user.type(screen.getByLabelText(/password/i), 'wrong');
    await user.click(screen.getByRole('button', { name: /sign in/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/invalid username or password/i);
  });
});
