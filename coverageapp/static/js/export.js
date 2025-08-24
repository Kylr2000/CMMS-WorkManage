document.addEventListener('DOMContentLoaded', function() {
    const exportButton = document.createElement('button');// Create pop up box
    exportButton.innerHTML = 'Export Data';
    exportButton.onclick = function() {
        const format = prompt('Please Select the file format (json/csv):');
        //Select data type radio or cellular
        const dataType = prompt('Please Select the data type (radio/cellular):');
        if ((format === 'json' || format === 'csv') && (dataType === 'radio' || dataType === 'cellular')) {
            exportData(format, dataType);
        } else {
            alert("Invalid format or data type entered! Please enter 'json' or 'csv' for format and 'radio' or 'cellular' for data type.");
        }
    };
    exportButton.classList.add('export-button');

    const container = document.createElement('div');
    container.appendChild(exportButton);

    document.body.appendChild(container);
});

function getCoverageData(dataType) {
    // Assuming radioData and cellularData are available in global scope
    if (dataType === 'radio') {
        return {
            radio: window.radioData
        };
    } else if (dataType === 'cellular') {
        return {
            cellular: window.cellularData
        };
    } else {
        console.log('Invalid data type selected.');
        return {};
    }
}


function exportData(format, dataType) {
    const data = getCoverageData(dataType);

    let dataStr;
    let mimeType;

    if (format === 'json') {
        dataStr = JSON.stringify(data, null, 4);
        mimeType = 'application/json';
    } else if (format === 'csv') {
        dataStr = convertToCSV(data);
        mimeType = 'text/csv';
    }

    if (!dataStr) {
        console.log('No data to export.');
        return;
    }

    const blob = new Blob([dataStr], {type: mimeType}); // Create a new Blob object using the data
    const url = URL.createObjectURL(blob); // Create a URL for the Blob object

    // Create a link element, set its href to the Blob URL, and programmatically click it to start the download
    const downloadLink = document.createElement('a');
    downloadLink.href = url;
    downloadLink.download = `coverage-data.${format}`;
    downloadLink.click();

    // Revoke the Blob URL after the download has started
    setTimeout(() => URL.revokeObjectURL(url), 100);
}

function convertToCSV(data) {
    function arrayToCSV(arr) {
        if (arr.length === 0) {
            console.log('No data to convert to CSV.');
            return '';
        }

        // Extracting the 'fields' from each object
        const extractedData = arr.map(item => item.fields);

        // Creating CSV string
        const array = [Object.keys(extractedData[0])].concat(extractedData);
        return array.map(it => Object.values(it).toString()).join('\n');
    }

    console.log('Data received for CSV conversion:', data);

    if (data.radio && data.cellular) {
        const radioCSV = arrayToCSV(data.radio);
        const cellularCSV = arrayToCSV(data.cellular);
        return radioCSV + '\n\n' + cellularCSV;
    } else if (data.radio) {
        return arrayToCSV(data.radio);
    } else if (data.cellular) {
        return arrayToCSV(data.cellular);
    } else {
        console.log('No radio or cellular data available.');
        return '';
    }
}
