// SweetAlert2 Configuration for CareHub
// Modern, clean alerts with border radius matching CareHub design

// Toast notifications (for success/info messages)
const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
        toast.addEventListener('mouseenter', Swal.stopTimer)
        toast.addEventListener('mouseleave', Swal.resumeTimer)
    },
    customClass: {
        popup: 'rounded-2xl shadow-2xl',
        timerProgressBar: 'bg-primary-600'
    }
});

// Confirmation dialogs (for delete/cancel actions)
const ConfirmDialog = Swal.mixin({
    customClass: {
        popup: 'rounded-2xl',
        title: 'text-2xl font-bold text-gray-900',
        htmlContainer: 'text-gray-600',
        confirmButton: 'bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-xl ml-2 transition-all',
        cancelButton: 'bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-3 px-6 rounded-xl mr-2 transition-all'
    },
    buttonsStyling: false,
    showCancelButton: true,
    confirmButtonText: 'Yes, proceed',
    cancelButtonText: 'Cancel',
    reverseButtons: true
});

// Success dialog (for successful operations)
const SuccessDialog = Swal.mixin({
    customClass: {
        popup: 'rounded-2xl',
        title: 'text-2xl font-bold text-gray-900',
        htmlContainer: 'text-gray-600',
        confirmButton: 'bg-primary-600 hover:bg-primary-700 text-white font-bold py-3 px-6 rounded-xl transition-all'
    },
    buttonsStyling: false,
    icon: 'success',
    confirmButtonText: 'OK'
});

// Error dialog (for errors)
const ErrorDialog = Swal.mixin({
    customClass: {
        popup: 'rounded-2xl',
        title: 'text-2xl font-bold text-gray-900',
        htmlContainer: 'text-gray-600',
        confirmButton: 'bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-xl transition-all'
    },
    buttonsStyling: false,
    icon: 'error',
    confirmButtonText: 'OK'
});

// Helper function to show flash messages as SweetAlert toasts
function showFlashMessage(message, type) {
    const icon = type === 'error' ? 'error' : type === 'warning' ? 'warning' : 'success';
    Toast.fire({
        icon: icon,
        title: message
    });
}

// Helper function for confirming destructive actions
async function confirmAction(title, text, confirmText = 'Yes, delete it!') {
    return await ConfirmDialog.fire({
        title: title,
        html: text,
        icon: 'warning',
        confirmButtonText: confirmText
    });
}

// Helper function for showing success
function showSuccess(title, text) {
    SuccessDialog.fire({
        title: title,
        html: text
    });
}

// Helper function for showing errors
function showError(title, text) {
    ErrorDialog.fire({
        title: title,
        html: text
    });
}
