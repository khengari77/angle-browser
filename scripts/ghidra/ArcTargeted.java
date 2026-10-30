// Targeted, persistent analysis of explicitly selected Arc function spans.
// @category ArcReverse
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.pcode.PcodeBlockBasic;
import com.google.gson.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;

public class ArcTargeted extends GhidraScript {
    private String at(Address a) { return "0x" + a.toString(); }
    private JsonObject reference(Reference ref) {
        JsonObject row = new JsonObject();
        row.addProperty("from", at(ref.getFromAddress()));
        row.addProperty("to", at(ref.getToAddress()));
        row.addProperty("kind", ref.getReferenceType().toString());
        Symbol symbol = currentProgram.getSymbolTable().getPrimarySymbol(ref.getToAddress());
        if (symbol != null) row.addProperty("target_symbol", symbol.getName(true));
        return row;
    }
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 3 || args.length % 2 != 1) {
            throw new IllegalArgumentException("Usage: ArcTargeted.java NEW_OUTPUT_DIR START END_EXCLUSIVE [START END_EXCLUSIVE ...]");
        }
        Path output = Paths.get(args[0]);
        Files.createDirectory(output); // Never silently overwrite a prior research run.
        JsonObject report = new JsonObject();
        report.addProperty("format", "arcreverse-ghidra-targeted-v1");
        report.addProperty("program", currentProgram.getName());
        report.addProperty("executable_sha256", currentProgram.getExecutableSHA256());
        report.addProperty("auto_analysis", false);
        JsonArray results = new JsonArray();
        report.add("functions", results);
        JsonArray limits = new JsonArray();
        limits.add("Only explicitly selected spans are disassembled; no whole-program auto-analysis ran.");
        limits.add("Callers and indirect calls may be absent; function signatures and inferred types are incomplete.");
        limits.add("Decompiler output is pseudocode, not recovered source or observed runtime behavior.");
        report.add("limitations", limits);
        DecompInterface decompiler = new DecompInterface();
        try {
            if (!decompiler.openProgram(currentProgram)) throw new IllegalStateException(decompiler.getLastMessage());
            for (int index=1; index<args.length; index+=2) {
                monitor.checkCancelled();
                Address start=toAddr(args[index]);
                Address end=toAddr(args[index+1]);
                long length=end.subtract(start);
                if (length <= 0 || length > 65536) throw new IllegalArgumentException("Span must be positive and <=64 KiB");
                AddressSet restriction=new AddressSet(start,end.subtract(1));
                JsonObject row=new JsonObject(); results.add(row);
                row.addProperty("start", at(start)); row.addProperty("end_exclusive", at(end));
                DisassembleCommand disasm=new DisassembleCommand(start, restriction, true);
                disasm.enableCodeAnalysis(false);
                row.addProperty("disassembled", disasm.applyTo(currentProgram,monitor));
                if (disasm.getStatusMsg()!=null) row.addProperty("disassembly_status",disasm.getStatusMsg());
                Function function=getFunctionAt(start);
                if (function == null) {
                    CreateFunctionCmd create=new CreateFunctionCmd(start);
                    if (create.applyTo(currentProgram,monitor)) function=create.getFunction();
                    else row.addProperty("function_creation_error",create.getStatusMsg());
                }
                JsonArray references=new JsonArray(); row.add("references",references);
                StringBuilder assembly=new StringBuilder();
                InstructionIterator instructions=currentProgram.getListing().getInstructions(restriction,true);
                int count=0;
                while (instructions.hasNext()) {
                    Instruction instruction=instructions.next(); count++;
                    assembly.append(at(instruction.getAddress())).append(" ").append(instruction.toString()).append("\n");
                    for (Reference ref:instruction.getReferencesFrom()) {
                        if (ref.getReferenceType().isCall() || ref.getReferenceType().isData()) references.add(reference(ref));
                    }
                }
                row.addProperty("instruction_count",count);
                Files.writeString(output.resolve(at(start)+".asm"),assembly.toString(),StandardCharsets.UTF_8);
                if (function != null) {
                    row.addProperty("function_name",function.getName());
                    row.addProperty("body_within_selected_span",restriction.contains(function.getBody()));
                    if (restriction.contains(function.getBody())) {
                        decompiler.flushCache();
                        DecompileResults result=decompiler.decompileFunction(function,45,monitor);
                        row.addProperty("decompile_completed",result.decompileCompleted());
                        row.addProperty("decompile_message",result.getErrorMessage());
                        JsonArray outside=new JsonArray();
                        if (result.getHighFunction()!=null) {
                            for (PcodeBlockBasic block:result.getHighFunction().getBasicBlocks()) {
                                if (!restriction.contains(block.getStart()) || !restriction.contains(block.getStop())) {
                                    JsonObject escaped=new JsonObject();escaped.addProperty("start",at(block.getStart()));escaped.addProperty("stop",at(block.getStop()));outside.add(escaped);
                                }
                            }
                        }
                        row.add("decompiler_blocks_outside_selected_span",outside);
                        if (result.decompileCompleted() && result.getDecompiledFunction()!=null) {
                            Files.writeString(output.resolve(at(start)+".c"),result.getDecompiledFunction().getC(),StandardCharsets.UTF_8);
                        }
                    }
                }
                Files.writeString(output.resolve("report.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report),StandardCharsets.UTF_8);
                println("ARC_TARGET_COMPLETE "+at(start));
            }
            report.addProperty("batch_completed",true);
            Files.writeString(output.resolve("report.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report),StandardCharsets.UTF_8);
        } finally { decompiler.dispose(); }
    }
}
