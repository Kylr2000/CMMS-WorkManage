function printPage() {
    window.print();
}

document.addEventListener('DOMContentLoaded', function() {
    const printButton = document.createElement('button');
    printButton.innerHTML = 'Print Page';
    printButton.onclick = printPage;
    printButton.classList.add('print-button');
    document.body.appendChild(printButton);
});