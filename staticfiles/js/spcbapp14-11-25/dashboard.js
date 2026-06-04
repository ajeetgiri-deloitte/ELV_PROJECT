window.addEventListener('pageshow', function(event) {
          if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
              // Reload or redirect when back button is pressed
              window.location.href = "{% url 'logout' %}";
          }
      });