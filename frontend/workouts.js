// Workouts page functionality
function selectProgram(programType) {
    // Add visual feedback
    const card = event.currentTarget;
    card.style.transform = 'scale(0.98)';
    
    setTimeout(() => {
        card.style.transform = '';
        
        // For now, just show an alert
        // Later this can redirect to a specific program page
        alert(`Selected: ${programType.toUpperCase()} program\n\nThis feature is coming soon!`);
        
        // You can add navigation logic here:
        // window.location.href = `program-${programType}.html`;
    }, 150);
}

// Add hover effects for program cards
document.addEventListener('DOMContentLoaded', function() {
    const programCards = document.querySelectorAll('.program-card');
    
    programCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});
