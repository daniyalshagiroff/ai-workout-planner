// Workouts page functionality
function selectProgram(programType) {
    const card = event.currentTarget;
    card.style.transform = 'scale(0.98)';
    
    setTimeout(() => {
        card.style.transform = '';
        if (programType === 'foundational') {
            window.location.href = '/static/program-foundational.html';
            return;
        }
        alert(`Selected: ${programType.toUpperCase()} program`);
    }, 120);
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
