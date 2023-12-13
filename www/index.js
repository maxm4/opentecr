/*
  Code inspired from: https://github.com/namieluss/csv-datatable-papaparse 
  Maxime Mahout
*/

const URL_CSV = 'https://raw.githubusercontent.com/maxm4/opentecr-data/main/core_scripts/TECRDB_noor.csv'
const URL_JSON = 'https://raw.githubusercontent.com/opentecr/opentecr-data/rgiessmann/first/data/10001/v1.0.0/data.json'  

document.addEventListener('DOMContentLoaded', function() { 

    Papa.parsePromise = function(file) {
        return new Promise(function(complete, error) {
            Papa.parse(file, {download: true, complete, skipEmptyLines: true})
        });
    };

    /* Asynchronous chain of events */
    Papa.parsePromise(URL_CSV)
    .then(result => {
        if (result.data && result.data.length > 0) {
            htmlTableGenerator(result.data)
        }
    })
    .then(() => {
        console.log("DataTable succesfully initialized");
    })
    .catch(() => {
        console.log("DataTable initialization failed");
    });

    fetch(URL_JSON)
    .then(result =>  {
            console.log(result.json()) /* returns data error */
        });
}, false);

async function htmlTableGenerator(content) {
    let data_preview = document.getElementById('data-preview');

    let html = '<table id="data-table" class="table table-condensed table-hover table-striped" style="width:100%">';

    if (content.length == 0 || typeof(content[0]) === 'undefined') {
        return new Promise(() => initDataTable([[]]))
    } else {
        const header = content[0];
        const data = content.slice(1);

        html += '<thead>';
        html += '<tr>';

        for (const colData of header) {
            html += '<th>' + colData + '</th>';
        }

        html += '</tr>';
        html += '</thead>';
        html += '<tbody>';

        html += '</tbody>';
        html += '</table>';

        // insert table element into csv preview
        data_preview.innerHTML = html;

        // initialise DataTable
        return new Promise(() => initDataTable(data)) 
    }
}

async function initDataTable(jsonData) {
    let div_height = $('.container').height()
    $('#data-table').dataTable({
        data: jsonData,
        columnDefs: [{
            "defaultContent": "-",
            "targets": "_all"
          }],
        scrollX: true,
        scrollY: false, /*div_height*/
        scrollCollapse: true,
        dom: 'Bfrtip',
        buttons: [
            'colvis',
        ]
    })
}
