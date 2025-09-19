// Test JavaScript file with various code quality issues
// This file is designed to demonstrate the code review bot capabilities

var users = [];
var activeUsers = [];

function getUserData(userId) {
    // Added input validation
    if (!userId || typeof userId !== 'string') {
        throw new Error('Invalid userId provided');
    }
    
    // Fixed SQL injection with parameterized query
    var query = "SELECT * FROM users WHERE id = ?";
    
    // Synchronous operation that could block
    var result = database.execute(query, [userId]);
    return result;
}

function processUsers(userList) {
    // Updated to use modern array methods
    const data = userList.filter(user => user.active === true);
    return data;
}

// Function with no error handling
function calculateTotal(items) {
    var total = 0;
    for(var i = 0; i < items.length; i++) {
        total += items[i].price;
    }
    return total;
}

// Inefficient DOM manipulation
function updateUserList(users) {
    var container = document.getElementById('user-list');
    container.innerHTML = ''; // Potential XSS if users contain HTML
    
    for(var i = 0; i < users.length; i++) {
        var userDiv = document.createElement('div');
        userDiv.innerHTML = '<span>' + users[i].name + '</span>'; // XSS vulnerability
        container.appendChild(userDiv);
    }
}

// Memory leak potential - event listeners not cleaned up
function attachEventListeners() {
    var buttons = document.querySelectorAll('.user-button');
    for(var i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener('click', function(e) {
            // Closure issue - 'i' will always be the last value
            console.log('Button ' + i + ' clicked');
            processUser(i);
        });
    }
}

// Function with magic numbers and poor naming
function calc(x, y) {
    if(x > 18) {
        return y * 0.85;
    } else {
        return y * 1.0;
    }
}

// Global variable pollution
window.appData = {
    version: '1.0',
    users: users,
    settings: null
};

// No proper module pattern or exports
console.log('App initialized');
