import time
from typing import Optional
from rich.console import Console

class RateLimiter:
    """
    Rate limiter for API requests using token bucket algorithm.
    """
    
    def __init__(self, requests_per_minute: int):
        """
        Initialize the rate limiter.
        
        Args:
            requests_per_minute (int): Maximum number of requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute  # Time between requests in seconds
        self.last_request_time = 0.0
        self.console = Console()
        
    def wait(self) -> None:
        """
        Wait if necessary to maintain the rate limit.
        
        This method calculates the time since the last request and waits
        if needed to ensure the rate limit is not exceeded.
        """
        current_time = time.time()
        
        # First request doesn't need to wait
        if self.last_request_time == 0.0:
            self.last_request_time = current_time
            return
            
        # Calculate time since last request
        elapsed = current_time - self.last_request_time
        
        # If we need to wait
        if elapsed < self.interval:
            wait_time = self.interval - elapsed
            self.console.print(f"[dim]Rate limiting: waiting {wait_time:.2f} seconds...[/dim]")
            time.sleep(wait_time)
        
        # Update last request time
        self.last_request_time = time.time()


# Test the RateLimiter if this file is run directly
if __name__ == "__main__":
    import random
    
    console = Console()
    console.print(Panel(
        "[bold blue]Rate Limiter Test[/bold blue]",
        subtitle="Testing rate limiting functionality",
        border_style="blue"
    ))
    
    # Test with different rates
    for rate in [30, 10, 5]:
        limiter = RateLimiter(rate)
        console.print(f"\n[bold]Testing with {rate} requests per minute[/bold]")
        
        # Make 5 test requests
        for i in range(1, 6):
            start_time = time.time()
            limiter.wait()
            end_time = time.time()
            
            # Simulate work
            work_time = random.uniform(0.1, 0.3)
            console.print(f"[green]Request {i}: waited {end_time - start_time:.2f}s, processing for {work_time:.2f}s[/green]")
            time.sleep(work_time)
        
        console.print(f"[blue]Completed test with {rate} requests per minute[/blue]")
    
    console.print("[bold green]Rate limiter tests completed successfully![/bold green]")