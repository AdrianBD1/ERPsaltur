// --- Funciones para Generar HTML de Filas ---

function crearInput(type, name, placeholder, onInput = null, readOnly = false) {
    const input = document.createElement("input");
    input.type = type;
    input.name = name;
    input.placeholder = placeholder;
    if (readOnly) input.readOnly = true;
    if (onInput) input.addEventListener("input", onInput);
    return input;
}

function agregarFilaCompra() {
    const container = document.getElementById("items-container");
    const row = document.createElement("div");
    row.className = "input-group";
    
    // Contenedor relativo para el autocompletado
    const nameWrapper = document.createElement("div");
    nameWrapper.className = "relative-container";
    nameWrapper.style.flex = "2";

    const idInput = document.createElement("input");
    idInput.type = "hidden";
    idInput.name = "id";

    const nameInput = crearInput("text", "nombre", "Nombre Producto (min 5 letras)", (e) => manejarAutocomplete(e.target, idInput, 'compra'));
    nameInput.autocomplete = "off";
    
    const listaSug = document.createElement("div");
    listaSug.className = "autocomplete-items";
    
    nameWrapper.appendChild(nameInput);
    nameWrapper.appendChild(listaSug);

    // Otros campos
    const precioInput = crearInput("number", "precio_compra", "Precio Compra", calcularTotal);
    const cantInput = crearInput("number", "cantidad", "Cantidad", calcularTotal);
    const totalInput = crearInput("number", "total", "Total", null, true);
    totalInput.style.backgroundColor = "#eee";

    // Unir todo
    row.appendChild(idInput);
    row.appendChild(nameWrapper);
    row.appendChild(precioInput);
    row.appendChild(cantInput);
    row.appendChild(totalInput);
    
    // Boton eliminar fila
    const btnDel = document.createElement("button");
    btnDel.innerText = "X";
    btnDel.style.background = "red"; btnDel.style.color="white"; btnDel.style.border="none"; btnDel.style.padding="10px";
    btnDel.onclick = () => container.removeChild(row);
    row.appendChild(btnDel);

    container.appendChild(row);
}

function agregarFilaVenta() {
    const container = document.getElementById("items-container");
    const row = document.createElement("div");
    row.className = "input-group";
    
    const nameWrapper = document.createElement("div");
    nameWrapper.className = "relative-container";
    nameWrapper.style.flex = "2";

    const idInput = document.createElement("input");
    idInput.type = "hidden";
    idInput.name = "id";

    const nameInput = crearInput("text", "nombre", "Buscar Producto...", (e) => manejarAutocomplete(e.target, idInput, 'venta'));
    nameInput.autocomplete = "off";
    
    const listaSug = document.createElement("div");
    listaSug.className = "autocomplete-items";
    
    nameWrapper.appendChild(nameInput);
    nameWrapper.appendChild(listaSug);

    // En venta registramos el precio al que vendemos
    const precioInput = crearInput("number", "precio_venta", "Precio Venta", calcularTotal);
    // Nota: Podrías hacer un fetch para traer el precio sugerido si quisieras
    const cantInput = crearInput("number", "cantidad", "Cantidad", calcularTotal);
    const totalInput = crearInput("number", "total", "Total", null, true);
    totalInput.style.backgroundColor = "#eee";

    row.appendChild(idInput);
    row.appendChild(nameWrapper);
    row.appendChild(precioInput);
    row.appendChild(cantInput);
    row.appendChild(totalInput);

    const btnDel = document.createElement("button");
    btnDel.innerText = "X";
    btnDel.style.background = "red"; btnDel.style.color="white";
    btnDel.onclick = () => container.removeChild(row);
    row.appendChild(btnDel);

    container.appendChild(row);
}

// --- Lógica de Negocio Frontend ---

function calcularTotal(e) {
    const row = e.target.parentElement;
    const precio = row.querySelector("input[name^='precio']").value;
    const cant = row.querySelector("input[name='cantidad']").value;
    const totalInput = row.querySelector("input[name='total']");
    
    if (precio && cant) {
        totalInput.value = (parseFloat(precio) * parseFloat(cant)).toFixed(2);
    }
}

async function manejarAutocomplete(input, idInput, modo) {
    const val = input.value;
    const list = input.nextElementSibling;
    list.innerHTML = "";
    
    if (val.length < 5 && modo === 'compra') return; 
    if (val.length < 3 && modo === 'venta') return; // En venta buscamos antes

    const res = await fetch(`/api/buscar-producto?q=${val}`);
    const datos = await res.json();

    datos.forEach(prod => {
        const item = document.createElement("div");
        item.innerHTML = `<strong>${prod.nombre}</strong> <small>(Stock: ${prod.stock})</small>`;
        item.addEventListener("click", function() {
            input.value = prod.nombre;
            idInput.value = prod.id;
            
            // Si es venta, podríamos autocompletar el precio
            const row = input.closest(".input-group");
            if(modo === 'venta' && prod.precio_venta) {
                row.querySelector("input[name='precio_venta']").value = prod.precio_venta;
            }
            
            list.innerHTML = "";
        });
        list.appendChild(item);
    });

    if (modo === 'compra') {
        const addItem = document.createElement("div");
        addItem.innerHTML = `<em>+ Agregar nuevo: "${val}"</em>`;
        addItem.style.color = "green";
        addItem.addEventListener("click", function() {
            idInput.value = ""; // ID vacío significa nuevo producto
            // input.value se queda con lo que escribió el usuario
            list.innerHTML = "";
        });
        list.appendChild(addItem);
    }
}

async function enviarFormulario(tipo) {
    if(!confirm("¿Estás seguro de registrar esta operación?")) return;

    const rows = document.querySelectorAll(".input-group");
    const payload = [];
    let valido = true;

    rows.forEach(row => {
        const id = row.querySelector("input[name='id']").value;
        const nombre = row.querySelector("input[name='nombre']").value;
        const cant = row.querySelector("input[name='cantidad']").value;
        const total = row.querySelector("input[name='total']").value;
        
        let precio = 0;
        if (tipo === 'compra') precio = row.querySelector("input[name='precio_compra']").value;
        else precio = row.querySelector("input[name='precio_venta']").value;

        if(!nombre || !cant || !precio) valido = false;

        payload.push({
            id: id,
            nombre: nombre,
            cantidad: cant,
            [tipo === 'compra' ? 'precio_compra' : 'precio_venta']: precio,
            total: total
        });
    });

    if (!valido) {
        alert("Por favor completa todos los campos");
        return;
    }

    const endpoint = tipo === 'compra' ? '/api/registrar-compra' : '/api/registrar-venta';
    
    const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        alert("Registrado con éxito");
        window.location.href = "/";
    } else {
        alert("Error al registrar");
    }
}

// --- Ordenar Tablas ---
function sortTable(n, type) {
    // Implementación básica de sort table w3schools logic simplificada
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.querySelector("table");
    switching = true;
    dir = "asc"; 
    while (switching) {
        switching = false;
        rows = table.rows;
        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            let xVal = x.innerHTML.toLowerCase();
            let yVal = y.innerHTML.toLowerCase();
            
            // Si es numérico (columna total, cantidad, precio)
            if (!isNaN(parseFloat(xVal)) && !isNaN(parseFloat(yVal))) {
                xVal = parseFloat(xVal);
                yVal = parseFloat(yVal);
            }

            if (dir == "asc") {
                if (xVal > yVal) { shouldSwitch = true; break; }
            } else if (dir == "desc") {
                if (xVal < yVal) { shouldSwitch = true; break; }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
            switchcount ++; 
        } else {
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}