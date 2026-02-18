const state = {
  recipes: [],
  ingredients: [],
};

function setActiveTab(tabId) {
  document.querySelectorAll('.tab-content').forEach((node) => node.classList.remove('active'));
  document.querySelectorAll('.pill-button').forEach((node) => node.classList.remove('active'));

  const tab = document.getElementById(tabId);
  if (tab) tab.classList.add('active');

  const navButton = document.querySelector(`.pill-button[data-tab="${tabId}"]`);
  if (navButton) navButton.classList.add('active');
}

function createIngredientSelect(selectedId = '') {
  const select = document.createElement('select');
  select.className = 'ingredient-select';

  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Selecciona ingrediente';
  select.appendChild(placeholder);

  state.ingredients.forEach((ingredient) => {
    const option = document.createElement('option');
    option.value = ingredient.id;
    option.textContent = ingredient.name;
    if (String(selectedId) === String(ingredient.id)) option.selected = true;
    select.appendChild(option);
  });

  return select;
}

function addIngredientRow(selectedId = '', grams = '') {
  const list = document.getElementById('ingredients-list');
  const row = document.createElement('div');
  row.className = 'ingredient-row';

  const select = createIngredientSelect(selectedId);
  const gramsInput = document.createElement('input');
  gramsInput.type = 'number';
  gramsInput.min = '0.1';
  gramsInput.step = '0.1';
  gramsInput.placeholder = 'g por 1kg';
  gramsInput.value = grams;

  row.appendChild(select);
  row.appendChild(gramsInput);
  list.appendChild(row);
}

function refreshIngredientSelects() {
  document.querySelectorAll('.ingredient-row .ingredient-select').forEach((selectNode) => {
    const selected = selectNode.value;
    const replacement = createIngredientSelect(selected);
    selectNode.replaceWith(replacement);
  });
}

async function fetchRecipes() {
  const res = await fetch('/api/recipes');
  state.recipes = await res.json();
  const select = document.getElementById('elaborate-recipe');
  select.innerHTML = '';
  state.recipes.forEach((recipe) => {
    const option = document.createElement('option');
    option.value = recipe.id;
    option.textContent = recipe.name;
    select.appendChild(option);
  });
}

async function fetchIngredients() {
  const order = document.getElementById('ingredient-order').value;
  const res = await fetch(`/api/ingredients?order=${order}`);
  state.ingredients = await res.json();

  const tableBody = document.getElementById('ingredients-table-body');
  tableBody.innerHTML = '';

  state.ingredients.forEach((item) => {
    const tr = document.createElement('tr');
    const presentText = item.present_in.length > 0 ? item.present_in.join(', ') : '-';
    tr.innerHTML = `
      <td>${item.name}</td>
      <td>${presentText}</td>
      <td><button class="danger" data-delete-ingredient="${item.id}">🗑</button></td>
    `;
    tableBody.appendChild(tr);
  });

  tableBody.querySelectorAll('[data-delete-ingredient]').forEach((button) => {
    button.addEventListener('click', () => deleteIngredient(button.dataset.deleteIngredient));
  });

  refreshIngredientSelects();
}

async function deleteIngredient(ingredientId) {
  const ok = confirm('¿Seguro que quieres borrar este ingrediente?');
  if (!ok) return;

  const res = await fetch(`/api/ingredients/${ingredientId}`, { method: 'DELETE' });
  if (!res.ok) {
    const error = await res.json();
    alert(error.error || 'No se pudo borrar el ingrediente');
    return;
  }

  await fetchIngredients();
}

async function createIngredient() {
  const input = document.getElementById('new-ingredient-name');
  const name = input.value.trim();
  if (!name) {
    alert('Escribe un nombre de ingrediente');
    return;
  }

  const res = await fetch('/api/ingredients', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });

  if (!res.ok) {
    const error = await res.json();
    alert(error.error || 'No se pudo crear ingrediente');
    return;
  }

  input.value = '';
  await fetchIngredients();
}

async function calculate() {
  const recipeId = document.getElementById('elaborate-recipe').value;
  const kg = document.getElementById('kg-input').value;
  if (!recipeId) return;

  const res = await fetch(`/api/recipes/${recipeId}/calculate?kg=${kg}`);
  if (!res.ok) return;

  const data = await res.json();
  const body = document.getElementById('calculation-body');
  body.innerHTML = '';
  data.result.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.ingredient}</td><td>${row.grams}</td>`;
    body.appendChild(tr);
  });
}

async function saveRecipe(event) {
  event.preventDefault();
  const rows = [...document.querySelectorAll('.ingredient-row')];
  const items = rows
    .map((row) => {
      const select = row.querySelector('select');
      const gramsInput = row.querySelector('input');
      return {
        ingredient_id: Number(select.value),
        grams_per_kg: Number(gramsInput.value),
      };
    })
    .filter((item) => item.ingredient_id > 0 && item.grams_per_kg > 0);

  const payload = {
    name: document.getElementById('recipe-name').value.trim(),
    notes: document.getElementById('recipe-notes').value.trim(),
    items,
  };

  const res = await fetch('/api/recipes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const error = await res.json();
    alert(error.error || 'Error al guardar receta');
    return;
  }

  event.target.reset();
  document.getElementById('ingredients-list').innerHTML = '';
  addIngredientRow();
  await fetchRecipes();
  await fetchIngredients();
  alert('Receta guardada correctamente');
}

function bindEvents() {
  document.querySelectorAll('.pill-button').forEach((button) => {
    button.addEventListener('click', () => setActiveTab(button.dataset.tab));
  });

  document.querySelectorAll('[data-tab-target]').forEach((button) => {
    button.addEventListener('click', () => setActiveTab(button.dataset.tabTarget));
  });

  document.getElementById('ingredient-order').addEventListener('change', fetchIngredients);
  document.getElementById('add-ingredient').addEventListener('click', () => addIngredientRow());
  document.getElementById('add-ingredient-master').addEventListener('click', createIngredient);
  document.getElementById('calculate-btn').addEventListener('click', calculate);
  document.getElementById('recipe-form').addEventListener('submit', saveRecipe);
}

async function init() {
  bindEvents();
  await fetchIngredients();
  addIngredientRow();
  await fetchRecipes();
  await calculate();
}

init();
