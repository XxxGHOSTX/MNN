"""
Output Handler Module

Formats and displays the final results from the MNN pipeline.
Presents the top-ranked sequences in a clean, numbered format.
"""


def output_results(sequences: list) -> None:
    """
    Output the top results from the pipeline.
    
    Displays up to the top 10 sequences in a numbered list format.
    Each sequence is printed with its rank number, making results easy to read.
    
    Format:
        1. {sequence}
        2. {sequence}
        ...
    
    Args:
        sequences: List of dictionaries containing:
            - 'sequence' (str): The sequence text
            - 'score' (float): The relevance score (not displayed)
            
    Returns:
        None (prints to stdout)
        
    Examples:
        >>> output_results([
        ...     {'sequence': 'BOOK 0: HELLO WORLD', 'score': 0.9},
        ...     {'sequence': 'BOOK 1: WORLD HELLO', 'score': 0.8}
        ... ])
        1. BOOK 0: HELLO WORLD
        2. BOOK 1: WORLD HELLO
    """
    # Limit to top 10 results
    top_sequences = sequences[:10]
    
    # Print each sequence with its rank number
    for rank, item in enumerate(top_sequences, start=1):
        sequence = item['sequence']
        print(f"{rank}. {sequence}")
