import json
import MeCab
import re
import sys
import copy

RESULT_JSON = "result.json"
def initialize_result_json():
	result_file = open(RESULT_JSON,"w")
	result_file.write("{\n\"pages\" : [ \n")
	result_file.close()

def get_origin_pages():
	if not sys.argv[1]:
		print("No Input Json")
		exit()
	origin_file = open(sys.argv[1],"r")
	origin_json = json.load(origin_file)
	origin_pages = origin_json["pages"]
	origin_file.close()
	return origin_pages

def format_lines(lines):
	union_text = ""
	zenkaku = "".join(chr(0xff01 + i) for i in range(94))
	hankaku = "".join(chr(0x21 + i) for i in range(94))
	zen_to_han = str.maketrans(zenkaku,hankaku)
	for line in lines:
		text = line.translate(zen_to_han)
		union_text += re.sub('。','\n',text)
		union_text += "\n"
	result_lines = union_text.split("\n")
	result_lines = result_lines
	return result_lines


def collect_nouns(body_lines):
	for_parse_text = ""
	for line in body_lines:
		if "https" in line:
			continue
		for_parse_text += line
	mecab_dictionary = MeCab.Tagger('-d /usr/lib/arm-linux-gnueabihf/mecab/dic/mecab-ipadic-neologd')
	mecab_dictionary.parse("")
	node = mecab_dictionary.parseToNode(for_parse_text)

	result_nouns = []
	while node:
		is_noun = node.feature.split(",")[0] == "名詞"
		is_num = is_noun and (node.feature.split(",")[1] == "数")
		is_legal_num = is_num and (len(node.surface) == 4)
		is_legal_word = is_noun and not(is_num) and not(node.feature.split(",")[1] == "代名詞") and (len(node.surface) >= 2)
		
		if is_legal_num or is_legal_word:
			legal_noun = node.surface
#			legal_noun = legal_noun.encode('utf-8', 'replace').decode()
			legal_noun = re.sub('[\s]','_',legal_noun)
			legal_noun = "#" + legal_noun + " "
			result_nouns.append(legal_noun)

		node = node.next
	result_nouns = list(set(result_nouns))
	copy_nouns = copy.copy(result_nouns)
	for noun in copy_nouns:
		if noun in for_parse_text:
			result_nouns.remove(noun)
	return result_nouns

def make_last_line(nouns):
	last_line = ""
	for noun in nouns:
		last_line += noun
	return last_line

def make_page_dictionary(body_lines):
	title_dictionary = {"title" : body_lines[0]}
	lines_dictionary = {"lines" : body_lines}
	page_dictionary = {**title_dictionary,**lines_dictionary}
	return page_dictionary

def add_page_result_json(page_dictionary):
	result_file = open(RESULT_JSON,"a")
	json.dump(page_dictionary,result_file,indent=2,ensure_ascii=False)
	result_file.write(",\n")
	result_file.close()

def finish_result_json():
	result_json = open(RESULT_JSON,"a")
	result_json.write("]\n}")
	result_json.close()

if __name__ == "__main__":
	initialize_result_json()
	origin_pages = get_origin_pages()
	for page in origin_pages:
		body_lines = format_lines(page["lines"])
		nouns = collect_nouns(body_lines)
		if len(nouns) > 0:
			last_line = make_last_line(nouns)
			body_lines.append(last_line)
		page_dictionary = make_page_dictionary(body_lines)
		add_page_result_json(page_dictionary)
	finish_result_json()
