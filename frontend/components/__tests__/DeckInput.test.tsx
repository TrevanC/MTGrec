import { render, screen, fireEvent } from '@testing-library/react';
import DeckInput from '../DeckInput';

describe('DeckInput', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders the deck input form', () => {
    render(
      <DeckInput
        onSubmit={mockOnSubmit}
        isLoading={false}
      />
    );

    expect(screen.getByText('Import Your Deck')).toBeInTheDocument();
    expect(screen.getByLabelText('Decklist')).toBeInTheDocument();
    expect(screen.getByText('Analyze Deck')).toBeInTheDocument();
  });

  it('calls onSubmit with decklist when form is submitted', () => {
    render(
      <DeckInput
        onSubmit={mockOnSubmit}
        isLoading={false}
      />
    );

    const textarea = screen.getByLabelText('Decklist');
    const submitButton = screen.getByText('Analyze Deck');

    fireEvent.change(textarea, { target: { value: '1 Sol Ring\n1 Lightning Bolt' } });
    fireEvent.click(submitButton);

    expect(mockOnSubmit).toHaveBeenCalledWith('1 Sol Ring\n1 Lightning Bolt');
  });

  it('disables submit when loading', () => {
    render(
      <DeckInput
        onSubmit={mockOnSubmit}
        isLoading={true}
      />
    );

    const submitButton = screen.getByText('Analyzing Deck...');
    expect(submitButton).toBeDisabled();
  });

  it('shows error message when provided', () => {
    render(
      <DeckInput
        onSubmit={mockOnSubmit}
        isLoading={false}
        error="Test error message"
      />
    );

    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('loads example deck when example button is clicked', () => {
    render(
      <DeckInput
        onSubmit={mockOnSubmit}
        isLoading={false}
      />
    );

    const exampleButton = screen.getByText('Load Example');
    fireEvent.click(exampleButton);

    const textarea = screen.getByLabelText('Decklist') as HTMLTextAreaElement;
    expect(textarea.value).toContain('Prosper, Tome-Bound');
  });
});