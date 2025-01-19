import math

MIN_COORDINATES = 100  # Minimum required coordinates
MAX_QUALITY_COORDINATES = 100000  # Number of coordinates for max score
MIN_QUALITY_SCORE = 0.01  # Score for minimum coordinates

def calculate_quality_score(unique_coordinates: int) -> float:
    """
    Calculate quality score using a logarithmic scale.
    
    Args:
        unique_coordinates: Number of unique coordinates
        
    Returns:
        float: Quality score between 0 and 1
    """
    if unique_coordinates < MIN_COORDINATES:
        return 0.0
        
    log_min = math.log(MIN_COORDINATES)
    log_max = math.log(MAX_QUALITY_COORDINATES)
    log_current = math.log(min(unique_coordinates, MAX_QUALITY_COORDINATES))
    
    # Calculate normalized score between MIN_QUALITY_SCORE and 1.0
    normalized_score = (log_current - log_min) / (log_max - log_min)
    quality_score = MIN_QUALITY_SCORE + ((1.0 - MIN_QUALITY_SCORE) * normalized_score)
    
    return min(1.0, max(0.0, quality_score))

def test_scores():
    """Print quality scores for different coordinate counts."""
    test_values = [100, 1000, 5000, 10000, 50000, 100000, 1000000]
    
    print("\nQuality Score Test Results:")
    print("-" * 50)
    print(f"{'Coordinates':>12} | {'Score':>8}")
    print("-" * 50)
    
    for coords in test_values:
        score = calculate_quality_score(coords)
        print(f"{coords:>12,d} | {score:>8.4f}")
    print("-" * 50)

# python -m my_proof.utils.scoring
if __name__ == "__main__":
    test_scores()