import Button from '../Button/Button';
import Input, { type InputProps } from '../Input/Input';
import './Form.css';

export interface LabelProps {
    text: string
}

export interface IFormLine {
    label: LabelProps,
    input: InputProps
}

export interface IFormContent extends Array<IFormLine> {}

interface IForm {
    className?: string,
    submitBtnName?: string,
    isLineGrid?: boolean,
    content: IFormContent
}

const Form = ({ className="", submitBtnName, isLineGrid=false, content }: IForm) => {

    return (
        <form className={`form ${className}`}>
            <div className="form-line-group">
                {
                    content.map((formLine: IFormLine) => {
                        const { label, input } = formLine;

                        return (
                            <div className={ isLineGrid ? "form-line-grid" : "form-line" }>
                                <label
                                    htmlFor={ input.id }
                                    className="form-line-label"
                                >
                                    { label.text }
                                </label>
                                <Input
                                    type={ input.type }
                                    name={ input.name }
                                    placeholder={ input.placeholder }
                                    value={ input?.value }
                                    id={ input.id }
                                />
                            </div>
                        );
                    })
                }
            </div>
            { submitBtnName ? <Button className="form__btn">{ submitBtnName }</Button> : "" }
        </form>
    );
};

export { Form };
