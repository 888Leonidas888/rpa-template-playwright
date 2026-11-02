// Logica de interaccion de interfaz de usuario con JavaScript Vanilla
document.addEventListener('DOMContentLoaded', () => {
  const btnRunVisible = document.getElementById('btnRunVisible');
  const btnRunHeadless = document.getElementById('btnRunHeadless');
  const btnConfig = document.getElementById('btnConfig');
  const btnClear = document.getElementById('btnClear');
  const inputItems = document.getElementById('inputItems');

  btnRunVisible?.addEventListener('click', () => {
    const items = inputItems.value.trim();
    console.log(`[RPA] Iniciando ejecucion visible para items: ${items || 'DEMO'}`);
    alert(`Iniciando ejecucion visible del bot.\nComando: python main.py run --items "${items || 'DEMO'}"`);
  });

  btnRunHeadless?.addEventListener('click', () => {
    const items = inputItems.value.trim();
    console.log(`[RPA] Iniciando ejecucion headless para items: ${items || 'DEMO'}`);
    alert(`Iniciando ejecucion en segundo plano.\nComando: python main.py run --items "${items || 'DEMO'}" --headless`);
  });

  btnConfig?.addEventListener('click', () => {
    alert('Para configurar credenciales seguras en Windows DPAPI, ejecute en su terminal:\npython main.py auth');
  });

  btnClear?.addEventListener('click', () => {
    if (confirm('¿Desea limpiar la base de datos de memoria SQLite?')) {
      alert('Para confirmar la limpieza, ejecute en su terminal:\npython main.py clear-memory');
    }
  });
});
