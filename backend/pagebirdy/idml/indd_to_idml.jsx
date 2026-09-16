/*
 * babel — INDD -> IDML (Adobe InDesign / InDesign Server).
 *
 * Opens a native .indd and exports it as .idml so the translate core (which
 * only understands the IDML zip/XML format) can run against it.
 *
 * Arguments (via app.scriptArgs — set by the caller):
 *   inddPath  absolute path to the source .indd
 *   idmlPath  absolute output path for the .idml
 */
function run() {
  var inddPath = app.scriptArgs.getValue("inddPath");
  var idmlPath = app.scriptArgs.getValue("idmlPath");

  var doc = app.open(File(inddPath));
  doc.exportFile(ExportFormat.INDESIGN_MARKUP, File(idmlPath));
  doc.close(SaveOptions.NO);
  return "ok";
}
run();
