function toggle_visibility(id) {
    var e = document.getElementById(id);
    if (e.style.display == 'block')
        e.style.display = 'none';
    else
        e.style.display = 'block';
}

const fromPage = new URLSearchParams(window.location.search).get('from');
console.log(fromPage)

document.addEventListener('DOMContentLoaded', function() {

    Papa.parsePromise = function(file) {
        return new Promise(function(complete, error) {
            Papa.parse(file, {download: true, complete, skipEmptyLines: 'greedy'})
        });
    };

    Papa.parsePromise(URL_CSV)
    .then(result => {
        if (result.data && result.data.length > 0) {
            const params = new URLSearchParams(window.location.search);
            const hasItem = params.has('item');

            if (hasItem) {
                document.getElementById('data-preview').style.display = 'none';
            }

            return htmlTableGenerator(result.data).then(() => {
                params.forEach((value, key) => {
                    if (key !== 'item') {
                        const colIndex = $('#data-table thead th').filter(function() {
                            return $(this).text().toLowerCase() === key.toLowerCase();
                        }).index();
                        if (colIndex >= 0) {
                            $('#data-table').DataTable().column(colIndex).search(value).draw();
                        }
                    }
                });

                if (hasItem) {
                    const itemVal = decodeURIComponent(params.get('item'));
                    const headers = $('#data-table thead th').map((i,el) => $(el).text()).get().slice(0,-1);
                    $('#data-table').DataTable().rows().every(function() {
                        var key = String(this.data()[0]);
                        var shortKey = key.includes('#') ? key.split('#').slice(1).join('#') : key;
                        if (shortKey === itemVal || key === itemVal) {
                            console.log(fromPage)
                            openRowDetail(headers, this.data(), fromPage);
                        }
                    });
                }
            });
        }
    })
    .then(() => { console.log("DataTable succesfully initialized"); })
    .catch(() => { console.log("DataTable initialization failed"); });

}, false);

async function htmlTableGenerator(content) {
    let data_preview = document.getElementById('data-preview');

    let html = '<table id="data-table" class="table table-condensed table-hover table-striped" style="width:100%">';

    if (content.length == 0 || typeof(content[0]) === 'undefined') {
        return new Promise(() => initDataTable([], []))
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

        data_preview.innerHTML = html;

        return initDataTable(header, data)
    }
}

function corsUrl(url) {
    return url.replace('https://raw.githubusercontent.com/', 'https://cdn.jsdelivr.net/gh/')
    .replace(/\/refs\/heads\//, '@');
}

function formatCell(val) {
    if (val.trim().startsWith('[')) {
        try {
            const list = eval(val);
            if (Array.isArray(list) && list.length > 0) {
                const ul = $('<ul>').css({'margin':0,'padding-left':'1.2em'});
                list.forEach(el => ul.append($('<li>').text(el)));
                return ul;
            } else {
                return $('<span>');
            }
        } catch(e) {}
    }
    // E.C. number -> KEGG
    if (/^\d+\.\d+\.\d+\.\d+$/.test(val)) {
        return $('<a>').attr({href: 'https://www.kegg.jp/entry/' + val, target:'_blank', rel:'noopener'}).text(val);
    }
    // images
    else if (/\.(jpg|jpeg|png|gif|webp|svg)(\?.*)?$|\/image$/i.test(val)) {
        return $('<img>').attr('src', corsUrl(val)).css({'maxWidth':'150px'});
    // links
    } else if (val.startsWith('http://') || val.startsWith('https://')) {
        const safeval = val.replace(/^http:\/\//i, 'https://');
        return $('<a>').attr({href: safeval, target:'_blank', rel:'noopener'}).text(safeval);
    // reaction equation: a + b = c + d
    } else if (/\+|=/.test(val) && val.includes('=')) {
        const $span = $('<span>');
        const sides = val.split('=');
        sides.forEach(function(side, si) {
            if (si > 0) $span.append($('<span>').text(' = '));
            const compounds = side.trim().split('+').map(s => s.trim());
            compounds.forEach(function(compound, ci) {
                if (ci > 0) $span.append($('<span>').text(' + '));
                const $a = $('<a>').attr({rel:'noopener'}); // target:'_blank'
                if (/^kegg:[A-Z]\d+/i.test(compound)) {
                    $a.attr('href', 'compounds.html?kegg=' + encodeURIComponent(compound));
                } else {
                    var currentPage = window.location.pathname.split('/').pop() + window.location.search;
                    $a.attr('href', 'compounds.html?item=' + encodeURIComponent(compound) + '&from=' + encodeURIComponent(currentPage));
                }
                $a.text(compound);
                $span.append($a);
            });
        });
        return $span;
    // pubchem and chebi
    } else if (/^[A-Za-z][A-Za-z0-9]+:[A-Za-z0-9]/.test(val)) {
        const normalized = val.replace(/^pubchem:/i, 'pubchem.substance:').replace(/^chebi:/i, 'CHEBI:');
        return $('<a>').attr({href: 'https://identifiers.org/' + normalized, target:'_blank', rel:'noopener'}).text(normalized);
    // else
    } else {
        return $('<span>').text(val);
    }
}

function displayPost() {
    $('#data-table td').each((i, item) => { // :not(:first-child)
        const $item = $(item);
        const val = $item.text().trim();
        if (val === '') return;
        $item.empty().append(formatCell(val));
    });

    $('#data-table img').on('load', function() {
        $('#data-table').DataTable().columns.adjust();
    });
}

async function initDataTable(headers, jsonData) {
    var table = $('#data-table').dataTable({
        data: jsonData,
        scrollX: true,
        scrollY: false,
        scrollCollapse: true,
        autoWidth: true,
        dom: 'Bfrtip',
        buttons: ['colvis'],
        fixedColumns: {
            rightColumns: 1,
            heightMatch: 'none'
        },
        title: 'Details',
        columnDefs: [
            {
                targets: 0,
                createdCell: function(td, cellData, rowData) {
                    $(td).closest('tr').css('cursor', 'pointer').on('click', function() {
                        openRowDetail(headers, rowData, null);
                    });
                }
                /* // button instead
                 *                    createdCell: function(td, cellData, rowData) {
                 *                        var btn = $('<button>More…</button><br/>').css({
                 *                            background: 'transparent',
                 *                            border: '1px solid #aed49a',
                 *                            borderRadius: '999px',
                 *                            color: '#2d7018',
                 *                            fontSize: '0.78rem',
                 *                            fontWeight: '500',
                 *                            padding: '3px 12px',
                 *                            cursor: 'pointer',
            });
    btn.on('click', function() { openRowDetail(headers, rowData); });
    $(td).prepend(btn);
            }, */
            }
        ],
        drawCallback: displayPost,
    });
    console.log('Initting');
    return Promise.resolve();
}

function openRowDetail(headers, rowData, fromPage) {
    document.getElementById('data-preview').style.display = 'none';
    document.querySelector('h1').style.display = '';

    var detail = document.createElement('div');
    detail.id = 'row-detail';

    var back = $('<button>← Back</button>').css({
        background: 'transparent',
        border: '1px solid #aed49a',
        borderRadius: '999px',
        color: '#2d7018',
        fontSize: '0.88rem',
        fontWeight: '500',
        padding: '5px 16px',
        cursor: 'pointer',
        marginBottom: '1.25rem',
    }).on('click', function() {
        if (fromPage) {
            window.location.href = fromPage;
        } else {
            detail.remove();
            document.getElementById('data-preview').style.display = '';
            document.querySelector('h1').style.display = '';
            history.pushState(null, '', window.location.pathname);
            $('#data-table').DataTable().columns.adjust();
        }
    });

    var table = $('<table>').css({'width':'100%','borderCollapse':'collapse','fontSize':'0.92rem'});
    headers.forEach(function(header, i) {
        var val = rowData[i] || '';
        var tr = $('<tr>').css('borderBottom','1px solid #f0f5eb');
        var th = $('<td>').text(header).css({'padding':'10px 14px 10px 0','color':'#3d6830','fontWeight':'600','fontSize':'0.78rem','textTransform':'uppercase','letterSpacing':'0.4px','whiteSpace':'nowrap','verticalAlign':'top','width':'35%'});
        var td = $('<td>').css({'padding':'10px 0','verticalAlign':'top','color':'#1e2c18'}).append(formatCell(val));
        tr.append(th).append(td);
        table.append(tr);
    });

    $(detail).append(back).append(table);
    $('.card').append(detail);

    // update url
    var itemKey = rowData[0].includes('#') ? rowData[0].split('#').slice(1).join('#') : rowData[0];
    history.pushState(null, '', '?item=' + encodeURIComponent(itemKey));
}
