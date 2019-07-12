from overrides import overrides
from allennlp.common.util import JsonDict
from allennlp.data import Instance
from allennlp.predictors.predictor import Predictor

@Predictor.register('multiqa_predictor')
class MultiQAPredictor(Predictor):
    def predict_json(self, json_dict: JsonDict) -> JsonDict:
        if 'header' in json_dict:
            return {}

        example = self._dataset_reader.combine_context(json_dict)

        predictions = []
        for question_chunks in self._dataset_reader.make_chunks(example, {'dataset_name':''}):
            question_instances = []
            for instance in self._dataset_reader.gen_question_instances(question_chunks):
                question_instances.append(instance)

            question_predictions = self.predict_batch_instance(question_instances)

            max_logit = -30
            final_question_pred = {}
            for pred in question_predictions:
                if pred['category'] != 'cannot_answer' and pred['category_logit'] > max_logit:
                    max_logit = pred['category_logit']
                    if pred['category'] == 'span':
                        final_question_pred['best_span_str'] = pred['best_span_str']
                    else:
                        # yes no
                        final_question_pred['best_span_str'] = pred['category']

            if max_logit == -30:
                final_question_pred['best_span_str'] = 'cannot_answer'

            # Leaving only the original question ID for this dataset in order to run the original eval script.
            final_question_pred['qid'] = pred['qid']
            if pred['qid'].find('_q_') > -1:
                final_question_pred['qid'] = final_question_pred['qid'].split('_q_')[1]
            predictions.append(final_question_pred)

        formated_predictions = {pred['qid']:pred['best_span_str'] for pred in predictions}
        return formated_predictions
