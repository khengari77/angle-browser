// Apply analyst-selected, bounded internal switch target sets to a saved program.
// @category ArcReverse
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.pcode.JumpTable;
import com.google.gson.*;
import java.nio.file.*;
import java.util.*;

public class ArcJumpTables extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if (args.length!=2) throw new IllegalArgumentException("Usage: ArcJumpTables.java MANIFEST NEW_REPORT_FILE");
        JsonObject manifest=JsonParser.parseString(Files.readString(Paths.get(args[0]))).getAsJsonObject();
        if (!currentProgram.getExecutableSHA256().equals(manifest.get("sha256").getAsString()))
            throw new IllegalArgumentException("Program hash mismatch");
        Path output=Paths.get(args[1]);
        if (Files.exists(output)) throw new IllegalArgumentException("Report exists");
        JsonObject report=new JsonObject();
        report.addProperty("sha256",currentProgram.getExecutableSHA256());
        report.addProperty("limitation","Analyst-selected target sets constrain decompilation; they do not prove exhaustive runtime switch cases or enum values.");
        JsonArray tables=new JsonArray();report.add("tables",tables);
        for (JsonElement element:manifest.getAsJsonArray("tables")) {
            JsonObject input=element.getAsJsonObject();
            Address start=toAddr(input.get("function").getAsString());
            Address branch=toAddr(input.get("branch").getAsString());
            Address table=toAddr(input.get("table").getAsString());
            Address end=toAddr(input.get("end_exclusive").getAsString());
            int count=input.get("entries").getAsInt();
            if (count<1 || count>256 || start.compareTo(branch)>0 || branch.compareTo(table)>=0 || table.add(count*4L).compareTo(end)>0)
                throw new IllegalArgumentException("Invalid bounded table coordinates");
            Function function=getFunctionAt(start);
            Instruction instruction=getInstructionAt(branch);
            if (function==null || instruction==null || !instruction.getFlowType().isComputed())
                throw new IllegalArgumentException("Expected an existing function and computed branch");
            ArrayList<Address> unique=new ArrayList<>();
            JsonArray entries=new JsonArray();
            // Validate all entries before changing the database.
            for (int i=0;i<count;i++) {
                Address slot=table.add(i*4L);
                int delta=currentProgram.getMemory().getInt(slot);
                Address target=table.add(delta);
                if (target.compareTo(start)<0 || target.compareTo(table)>=0)
                    throw new IllegalArgumentException("Selected table target escapes code span");
                JsonObject row=new JsonObject();row.addProperty("index",i);row.addProperty("slot","0x"+slot);row.addProperty("target","0x"+target);entries.add(row);
                if (!unique.contains(target)) unique.add(target);
            }
            for (Address target:unique) {
                DisassembleCommand command=new DisassembleCommand(target,new AddressSet(start,table.subtract(1)),true);
                command.enableCodeAnalysis(false);
                if (!command.applyTo(currentProgram,monitor) && getInstructionAt(target)==null)
                    throw new IllegalStateException("Failed disassembling "+target);
                instruction.addOperandReference(0,target,RefType.COMPUTED_JUMP,SourceType.USER_DEFINED);
            }
            new JumpTable(branch,unique,true,0).writeOverride(function);
            CreateFunctionCmd.fixupFunctionBody(currentProgram,function,monitor);
            JsonObject row=new JsonObject();row.add("selection",input);row.add("entries",entries);row.addProperty("unique_targets",unique.size());tables.add(row);
        }
        Files.writeString(output,new GsonBuilder().setPrettyPrinting().create().toJson(report),StandardOpenOption.CREATE_NEW);
    }
}
