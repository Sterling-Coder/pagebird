/*
 * babel — IDML -> INDD (Adobe InDesign / InDesign Server).
 *
 * Opens an IDML file and saves it as a native .indd. InDesign reflows the
 * (now translated) text on open, so layout fidelity is preserved.
 *
 * Desktop InDesign:   File > Scripts, or  app.doScript(File(jsx))
 * InDesign Server:    invoked via SOAP/CLI with arguments below.
 *
 * Arguments (via app.scriptArgs — set by the caller):
 *   idmlPath  absolute path to the translated .idml
 *   inddPath  absolute output path for the .indd
 */
function run() {
  var idmlPath = app.scriptArgs.getValue("idmlPath");
  var inddPath = app.scriptArgs.getValue("inddPath");

  var doc = app.open(File(idmlPath));
  doc.save(File(inddPath));
  doc.close(SaveOptions.NO);
  return "ok";
}
run();
