     function toggle_visibility(id) {
        var e = document.getElementById(id);
        if (e.style.display == 'block')
            e.style.display = 'none';
        else
            e.style.display = 'block';
      }

      const URL_CSV = 'https://raw.githubusercontent.com/maxm4/hackathon-2025/refs/heads/main/maxime/final_compound_csv.csv';

      document.addEventListener('DOMContentLoaded', function() { 

      Papa.parsePromise = function(file) {
          return new Promise(function(complete, error) {
              Papa.parse(file, {download: true, complete, skipEmptyLines: 'greedy'})
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
        
      function displayImg() {
      
         $('#data-table td').each((i, item) => {
           const $item = $(item);
           var url = $item.text();
           if (url.startsWith('https://')){
               $item.empty();
               $item.append($('<img style="max-width:150px;"></img>').attr('src', url));
           }
         })   
      
      }

      async function initDataTable(jsonData) {
          let div_height = $('.container').height();
          var table = $('#data-table').dataTable({
              data: jsonData,
              scrollX: true,
              scrollY: false, /*div_height*/
              scrollCollapse: true,
              dom: 'Bfrtip',
              buttons: [
                  'colvis',
              ],
              drawCallback: displayImg,
          });
          console.log('Initting');
        }
        