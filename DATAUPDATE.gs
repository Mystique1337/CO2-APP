function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('CO2 Emissions')
      .addItem('Start Updating', 'startUpdating')
      .addItem('Stop Updating', 'stopUpdating')
      .addToUi();
}

function startUpdating() {
  const intervalMinutes = 1; // Update every minute
  
  // Check if the trigger already exists to avoid duplicates
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() == "updateCO2Emissions") {
      return;
    }
  }
  
  ScriptApp.newTrigger('updateCO2Emissions')
    .timeBased()
    .everyMinutes(intervalMinutes)
    .create();
}

function stopUpdating() {
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() == "updateCO2Emissions") {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

function updateCO2Emissions() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const locations = ['Artillery', 'Borikiri', 'Choba Junction', 'Eleme Junction', 'Garrison', 'Mile 1', 'Mile 3', 'Rumuola'];
  const now = new Date();
  const formattedDate = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');

  const data = locations.map(location => {
    const emissions = (Math.random() * (700 - 450) + 450).toFixed(4);
    return [location, formattedDate, emissions];
  });

  sheet.getRange(sheet.getLastRow() + 1, 1, data.length, data[0].length).setValues(data);
}
