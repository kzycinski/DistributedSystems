import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.net.DatagramPacket;
import java.net.InetAddress;
import java.net.MulticastSocket;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;

public class Logger {

    private static int BUFFER_LENGTH = 512;
    private static int DEST_PORT= 9000;
    private static String MCAST_ADDR = "230.0.0.0";


    public static void appendStrToFile(String fileName, String str)
    {
        try {
            BufferedWriter out = new BufferedWriter(new FileWriter(fileName, true));
            out.write(str);
            out.write("\n");
            out.close();
        }
        catch (IOException e) {
            e.printStackTrace();
        }
    }
    public static void main(String[] args) throws IOException {
    	String fileName = args[0];
    	System.out.println(fileName);
        byte[] b = new byte[BUFFER_LENGTH];
        DatagramPacket dgram = new DatagramPacket(b, b.length);
        MulticastSocket socket = new MulticastSocket(DEST_PORT);
        socket.joinGroup(InetAddress.getByName(MCAST_ADDR));
        while(true) {
            socket.receive(dgram);
            String res = new String(dgram.getData());
            System.err.println(res + "\n");
            dgram.setLength(b.length);
            appendStrToFile(fileName, res);
        }
    }
}
