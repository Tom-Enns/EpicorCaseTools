import re


class MeetingParserService:

    @staticmethod
    def remove_timestamps(file_path):
        speaker_pattern = r'<v (.*?)>'
        timestamp_pattern = r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}'

        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        cleaned_content = ''
        current_speaker = None
        current_text = ''

        for line in lines:
            # Remove timestamps
            line = re.sub(timestamp_pattern, '', line)
            # Remove </v>
            line = re.sub('</v>', '', line)

            match = re.search(speaker_pattern, line)
            if match:
                speaker = match.group(1)
                if speaker == current_speaker:
                    # Same speaker, append the text
                    current_text += ' ' + line[match.end():].strip()
                else:
                    # Different speaker, add the current text to cleaned_content and start a new text
                    if current_speaker is not None:
                        cleaned_content += f'<v {current_speaker}>{current_text}\n'
                    current_speaker = speaker
                    current_text = line[match.end():].strip()
            else:
                # No speaker, append the line to the current text
                current_text += ' ' + line.strip()

        # Add the last text
        if current_speaker is not None:
            cleaned_content += f'<v {current_speaker}>{current_text}\n'

        return cleaned_content

    @staticmethod
    def convert_vtt_to_txt(vtt_path):
        txt_path = vtt_path.replace('.vtt', '.txt')

        with open(vtt_path, 'r', encoding='utf-8') as vtt_file:
            lines = vtt_file.readlines()

        # Remove the VTT file specific lines (like WEBVTT, NOTE, etc.)
        lines = [line for line in lines if not line.strip().startswith(('WEBVTT', 'NOTE'))]

        with open(txt_path, 'w', encoding='utf-8') as txt_file:
            txt_file.writelines(lines)

        return txt_path
