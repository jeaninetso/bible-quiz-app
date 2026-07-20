import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders the hub title and a backend status indicator', async () => {
    render(<App />);
    expect(screen.getByText(/grow your bible knowledge/i)).toBeInTheDocument();
    expect(await screen.findByRole('status')).toBeInTheDocument();
  });
});
