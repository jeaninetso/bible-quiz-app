import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProtectedHome } from './ProtectedHome';

describe('ProtectedHome', () => {
  it('greets the user and calls onLogout when clicked', async () => {
    const onLogout = vi.fn();
    const user = userEvent.setup();
    render(<ProtectedHome user={{ username: 'jeanine' }} onLogout={onLogout} />);

    expect(screen.getByText(/welcome back/i)).toHaveTextContent('jeanine');
    await user.click(screen.getByRole('button', { name: /sign out/i }));
    expect(onLogout).toHaveBeenCalled();
  });
});
