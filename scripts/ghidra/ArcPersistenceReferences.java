// Read-only, bounded query of an existing analysis database. No decompilation.
// SPDX-License-Identifier: MPL-2.0
// @category ArcReverse
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import com.google.gson.*;
import java.nio.file.*;
public class ArcPersistenceReferences extends GhidraScript {
 public void run() throws Exception {
  JsonObject root=new JsonObject();
  root.addProperty("format","angle-persistence-references-v1");
  root.addProperty("executable_sha256",currentProgram.getExecutableSHA256());
  root.addProperty("auto_analysis",false);
  root.addProperty("decompilation",false);
  JsonArray sites=new JsonArray();root.add("sites",sites);
  for(String value:new String[]{"100f41540","103373b00","103374605","103374692","1033746c7","1033746e1"}) {
   monitor.checkCancelled();Address address=toAddr(value);JsonObject row=new JsonObject();sites.add(row);
   row.addProperty("address","0x"+address);Function fn=getFunctionContaining(address);
   if(fn!=null){row.addProperty("containing_function","0x"+fn.getEntryPoint());row.addProperty("function_name",fn.getName());}
   JsonArray incoming=new JsonArray();row.add("incoming",incoming);
   ReferenceIterator refs=currentProgram.getReferenceManager().getReferencesTo(address);
   int limit=0;while(refs.hasNext() && limit++<128){Reference ref=refs.next();JsonObject r=new JsonObject();r.addProperty("from","0x"+ref.getFromAddress());r.addProperty("kind",ref.getReferenceType().toString());Function caller=getFunctionContaining(ref.getFromAddress());if(caller!=null)r.addProperty("containing_function","0x"+caller.getEntryPoint());incoming.add(r);}
   row.addProperty("incoming_truncated",refs.hasNext());
   JsonArray outgoing=new JsonArray();row.add("outgoing",outgoing);Instruction instruction=getInstructionAt(address);
   if(instruction!=null)for(Reference ref:instruction.getReferencesFrom()){JsonObject r=new JsonObject();r.addProperty("to","0x"+ref.getToAddress());r.addProperty("kind",ref.getReferenceType().toString());Symbol symbol=currentProgram.getSymbolTable().getPrimarySymbol(ref.getToAddress());if(symbol!=null)r.addProperty("symbol",symbol.getName(true));outgoing.add(r);}
  }
  root.addProperty("limitations","Only existing Listing and ReferenceManager state queried. Missing references do not establish absence of callers. No argument value-flow or runtime execution observed.");
  Files.writeString(Paths.get(getScriptArgs()[0]),new GsonBuilder().setPrettyPrinting().create().toJson(root)+"\n");
 }
}
