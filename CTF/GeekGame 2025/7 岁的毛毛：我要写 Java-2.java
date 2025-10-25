import java.lang.foreign.Arena;
import java.lang.foreign.FunctionDescriptor;
import java.lang.foreign.Linker;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.SymbolLookup;
import java.lang.foreign.ValueLayout;
import java.lang.invoke.MethodHandle;
import java.nio.charset.StandardCharsets;

public class Solution {
    public static Object solve(Object si) throws Throwable {
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();

        MemorySegment getenvAddr = stdlib.find("getenv")
            .orElseThrow(() -> new RuntimeException("Cannot find getenv function"));

        FunctionDescriptor getenvDesc = FunctionDescriptor.of(
            ValueLayout.ADDRESS,
            ValueLayout.ADDRESS
        );

        MethodHandle getenv = linker.downcallHandle(getenvAddr, getenvDesc);

        try (Arena arena = Arena.ofConfined()) {
            String envVarName = "FLAG2";
            byte[] envVarBytes = envVarName.getBytes(StandardCharsets.UTF_8);
            MemorySegment sourceSegment = MemorySegment.ofArray(envVarBytes);
            MemorySegment destSegment = arena.allocate(envVarBytes.length + 1);
            MemorySegment.copy(sourceSegment, 0, destSegment, 0, envVarBytes.length);
            destSegment.set(ValueLayout.JAVA_BYTE, envVarBytes.length, (byte) 0);
            
            MemorySegment resultAddr = (MemorySegment) getenv.invokeExact(destSegment);

            if (resultAddr.address() == 0) {
                return "FLAG2 not found";
            }
            
            // --- START OF FIX ---
            // The MemorySegment returned from a native call is "unsized" (size 0).
            // We must give it a new size (spatial bound) so that methods like getString()
            // can safely access the memory it points to. 256 is an arbitrary but safe size.
            MemorySegment sizedResultAddr = resultAddr.reinterpret(256);
            // --- END OF FIX ---
            
            // Now call getString on the "sized" segment
            String flag = sizedResultAddr.getString(0);
            return flag;
        }
    }
}
