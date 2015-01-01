
// Right this in java that way  I don't have to re-write it.

/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */

package src.test;

import java.util.Iterator;
import org.sodbeans.phonemic.*;
import org.sodbeans.phonemic.tts.*;
import java.io.*;
/**
 * The TextToSpeech interface represents all functions that must be implemented
 * by supported Text To Speech engines. If a particular function is not
 * supported, the function should fail gracefully.
 *
 * @author Andreas Stefik and Jeff Wilson
 */
public class TestTTS implements TextToSpeech{
    private FileOutputStream outStream = null;
    private final boolean canPause = false;
    private final boolean canResume = false;
    private final boolean canStop = true;
    private final boolean canSetVoice = true;
    private final boolean canBlock = true;
    private final boolean canSetSpeed = true;
    private final boolean canSetPitch = false;
    private final boolean canSetVolume = true;
    private boolean speechEnabled = true;

    private boolean isSpeaking = false;
    
    private double speed;
    private double volume;
    private double pitch;
    private double version;

    private SpeechVoice voice;
    private TextToSpeechEngine textToSpeechEngine;

    private Iterator<SpeechVoice> availableVoicesIterator ;
    private Iterator<TextToSpeechEngine> textToSpeechEngineIterator ;
 
    private static final String testLogFileName = "PhonimTest.log";

    private String lastSpeech;
    public TestTTS() {
        speed = .5;
        volume = .5;
        pitch = .5;
        version = 1.5; 
        lastSpeech = null;
        File file = new File(testLogFileName);
        file.delete(); // delete if it exists
    }
    /**
     * Text goes at the end. form is field1,field2,...,#TEXT
     */

    public static TextToSpeech getTextToSpeech() { return new TestTTS(); } 
    public static void main(String[] args) { System.out.println("main");}
    public boolean writeToFile(String s) {
try {
    PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter(testLogFileName, true)));
    out.println(s);
    System.out.println(s);
    out.close();
    lastSpeech = s;
} catch (IOException e) {
            System.out
                .println("Error writing " + s + ",\n" + e.getLocalizedMessage());
}
return false;
/*
        if (outStream == null) {
            outStream = new FileOutputStream(fileName);
       try(PrintWriter out = new PrintWriter(new BufferedWriter(new FileWriter("myfile.txt", true)))) {
           out.println("the text");
           }catch (IOException e) {
            System.out
                .println("Error writing " + s + ",\n" + e.getLocalizedMessage());
           }

        }
        try {
            outStream.write(s);
        }
        catch (IOException e) {
            System.out
                .println("Error writing " + s + ",\n" + e.getLocalizedMessage());
        } 
*/
    }

    /**
     * Determines of the engine can speak blocking calls.
     *
     * @return boolean
     */
    public boolean canBlock() {
        return canBlock;
    }

    /**
     * Determines whether the text to speech engine can pause speech that is
     * currently being spoken.
     *
     * @return  boolean
     */
    public boolean canPause() {
        return canPause;
    }

    /**
     * Determines whether the text to speech engine can resume paused speech.
     *
     * @return
     */
    public boolean canResume() {
        return canResume;
    }

    /**
     * Determines whether the text to speech engine can stop speech.
     *
     * @return
     */
    public boolean canStop() { 
        return canStop;
    }

    /**
     * Determines whether the text to speech engine can set the current voice.
     *
     * @return
     */
    public boolean canSetVoice() {
        return canSetVoice;
    }

    /**
     * Determines whether the volume can be set for this text to speech engine.
     *
     * @return
     */
    public boolean canSetVolume() {
        return canSetVolume; 
    }

    /**
     * Determines whether the speed the speech is read can be set for the
     * text to speech engine.
     *
     * @return
     */
    public boolean canSetSpeed() {
        return canSetSpeed; 
    }

    /**
     * Determines whether the engine supports pitch changes.
     *
     * @return
     */
    public boolean canSetPitch() {
        return canSetPitch;
    }
    
    /**
     * Get all available voices for use by the text to speech engine.
     *
     * @return available voices
     */
    public Iterator<SpeechVoice> getAvailableVoices() {
        return availableVoicesIterator;
    }

    /**
     * Get the current voice in use by the text to speech engine.
     *
     * @return the current voice
     */
    public SpeechVoice getCurrentVoice() {
        return voice;
    }

    /**
     * Gets the current speed. (0.0 - 1.0)
     *
     * @return the speed
     */
    public double getSpeed() {
        return speed;
    }

    /**
     * Returns an enumerated type representing the current text to speech engine
     * that is loaded on the system.
     * 
     * @return the current text to speech engine
     */
    public TextToSpeechEngine getTextToSpeechEngine() {
        return textToSpeechEngine;
    }
    
    /**
     * Sets the text to speech engine to be used by the system. Note that
     * after this function is called, all settings will be lost, such as
     * speed, pitch, volume and voice.
     * 
     * @param engine
     * @return true if the engine was changed successfully, false otherwise.
     */
    public boolean setTextToSpeechEngine(TextToSpeechEngine engine) {
        textToSpeechEngine = engine;
        return true;
    }
    
    /**
     * Returns the available engines on the system.
     * 
     * @return 
     */
    public Iterator<TextToSpeechEngine> getAvailableEngines() {
        return textToSpeechEngineIterator;
    }
    /**
     * Gets the current volume. (0.0 - 1.0)
     *
     * @return the volume
     */
    public double getVolume() {
        return volume;
    }

    /**
     * Gets the current pitch. (0.0 - 1.0)
     *
     * @return the pitch
     */
    public double getPitch() { return pitch; }
    
    /**
     * Determines whether or not the engine is currently speaking.
     * Not supported by all engines. If not supported, false is always
     * returned.
     *
     * @return whether or not the engine is speaking
     */
    public boolean isSpeaking() { return isSpeaking;}

    /**
     * Pauses current speech (if any).
     *
     * @return indicates success or failure.
     */
    public boolean pause() { return canPause; }
    
    /**
     * Reinitializes the text to speech engine.
     */
    public void reinitialize() {
        return ; // reset defaults?
    }

    /**
     * Respeaks the most recently uttered text.
     *
     * @return indicates success or failure.
     */
    public boolean respeak() {
        if (this.lastSpeech != null) {
            this.speak(lastSpeech);
            return true;
        }
        else return false;
    }

    
    /**
     * Copies the most recently uttered text to the clipboard.
     * 
     * @return indicates success or failure
     */
    public boolean copyToClipboard() {
        return false;
    }
    
    /**
     * Resumes current speech, if any is currently paused.
     *
     * @return indicates success or failure.
     */
    public boolean resume() {
        return canResume;
    }

    /**
     * Sets the current volume. (0.0 - 1.0)
     *
     * @param vol the new volume
     * @return indicates success or failure.
     */
    public boolean setVolume(double vol) {
        if (canSetVolume)  {
            this.volume = vol; 
            return true;
        } else return false;
    }
        

    /**
     * Sets the current speed. (0.0 - 1.0)
     *
     * @param speed the new speed
     * @return indicates success or failure.
     */
    public boolean setSpeed(double speed) {
        if (canSetSpeed) {
            this.speed = speed;
            return true;
        } else return false;
    }

    /**
     * Sets the current pitch. (0.0 - 1.0)
     *
     * @param speed the new speed
     * @return indicates success or failure.
     */
    public boolean setPitch(double pitch) {
        if (canSetPitch) {
            this.pitch = pitch;
            return true;
        } else return false;
    }

    /**
     * Set the current voice.
     *
     * @param voice the new voice
     * @return indicates success or failure.
     */
    public boolean setVoice(SpeechVoice voice) {
        if (canSetVoice) {
            this.voice = voice;
            return true;
        } else return false;
    }

    /**
     * Speaks the given string.
     *
     * @param text The string to speak.
     * @return indicates success or failure.
     */
    public boolean speak(String text) {
        return writeText(text, false, SpeechPriority.MEDIUM, RequestType.TEXT);
 }
    public boolean writeText(final String text, final boolean isBlocking, final SpeechPriority priority, final RequestType rt) {
        // write pitch, voice, volume, speed, blocking?, text
        String outText = "";
        outText += isBlocking + "," +  pitch + "," + priority + "," + rt + "," + speed + "," + voice + ","+  volume  + '#' + text ;
        return writeToFile(outText);
 }
    public boolean writeText(final char c, final boolean isBlocking, final SpeechPriority priority, final RequestType rt) {
        // write pitch, voice, volume, speed, blocking?, text
        String outText = "";
        outText += isBlocking + "," +  pitch + "," + priority + "," + rt + "," + speed + "," +  voice + "," + volume + '#' +  c;
        return writeToFile(outText);
    } 
    /**
     * Speaks the given string with the given priority.
     *
     * @param text The string to speak.
     * @param priority Priority to assign to given text.
     * @return indicates success or failure.
     */
    public boolean speak(String text, SpeechPriority priority) {
        return writeText(text, false, priority, RequestType.TEXT);
    }

    /**
     * Speaks the given string with the given priority.
     *
     * @param text The string to speak.
     * @param priority Priority to assign to given text.
     * @param type A TEXT or CHARACTER request
     * @return indicates success or failure.
     */
    public boolean speak(String text, SpeechPriority priority, RequestType type) {
        return writeText(text, false, priority, type);
    }

    /**
     * Speaks the given character. Characters are
     * spoken differently by various engines. On OS X, for example, characters
     * are spoken with a higher pitch if they are capitalized letters.
     *
     * @param c The character to speak.
     * @return indicates success or failure.
     */
    public boolean speak(char c) {
        return writeText(c, false, SpeechPriority.MEDIUM, RequestType.CHARACTER);
      }
        
    
    /**
     * Speaks the given character with the given priority. Characters are
     * spoken differently by various engines. On OS X, for example, characters
     * are spoken with a higher pitch if they are capitalized letters.
     *
     *
     * @param c The character to speak.
     * @param priority Priority to assign to given text.
     * @return indicates success or failure.
     */
    public boolean speak(char c, SpeechPriority priority) {
        return writeText(c, false, priority, RequestType.CHARACTER);
    }

    /**
     * Speak using the SpeechProcessor proc.
     *
     * @param proc
     * @return
     */
    public boolean speak(SpeechProcessor proc) { return false; } // not implementned don't knwo what it does
    
    /**
     * Speaks the given string and blocks until speaking is complete.
     *
     * @param text The string to speak.
     * @return indicates success or failure.
     */
    public boolean speakBlocking(String text) {
        return writeText(text, true, SpeechPriority.MEDIUM, RequestType.TEXT);
    }


    /**
     * Speaks the given string with given priority and blocks until speaking
     * is complete.
     *
     * @param text The string to speak.
     * @param priority Priority to assign to given text.
     * @return indicates success or failure.
     */
    public boolean speakBlocking(String text, SpeechPriority priority) {
        return writeText(text, true, priority, RequestType.TEXT);
    }

    /**
     * Speaks the given string with given priority and blocks until speaking
     * is complete.
     *
     * @param text The string to speak.
     * @param priority Priority to assign to given text.
     * @param type A TEXT or CHARACTER request
     * @return indicates success or failure.
     */
    public boolean speakBlocking(String text, SpeechPriority priority, RequestType type) {

        return writeText(text, true, priority, RequestType.TEXT);
    }
    
    /**
     * Speaks the given character. Works exactly like speak(char), but blocks
     * until speaking is finished.
     *
     * @param c The character to speak.
     * @return indicates success or failure.
     */
    public boolean speakBlocking(char c) { return writeText(c, true, SpeechPriority.MEDIUM, RequestType.CHARACTER); }

    /**
     * Speaks the given character. Works exactly like speak(char), but blocks
     * until speaking is finished.
     *
     * @param c The character to speak.
     * @param priority Priority to assign to given text.
     * @return indicates success or failure.
     */
    public boolean speakBlocking(char c, SpeechPriority priority) {
        return writeText(c, true, priority, RequestType.CHARACTER) ;
}
    /**
     * Stops current speech (if any).
     *
     * @return indicates success or failure.
     */
    public boolean stop() { return canStop; }
    
    /**
     * Set whether or not speech is enabled. If speech is disabled, all
     * speak calls will be ignored.
     * @param enabled 
     */
    public void setSpeechEnabled(boolean enabled) { this.speechEnabled =  speechEnabled; } 
    
    /**
     * Returns whether or not speech is currently enabled. By default, speech
     * is enabled.
     * @return 
     */
    public boolean isSpeechEnabled() { return speechEnabled; } 
    
    /**
     * Get the phonemic version being used by this instance of TextToSpeech. If
     * this instance is connected to a server, this returns the server's Phonemic
     * version.
     * 
     * @return 
     */
    public double getVersion() { return version; }
}
