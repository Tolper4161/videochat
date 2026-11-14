import { Form, type IFormContent } from '../Form/Form';

interface IRoomOptionsForm {
    className?: string
}

const RoomOptionsForm = ({ className="" }: IRoomOptionsForm) => {
    const content: IFormContent = [
        {
            label: { text: "Title" },
            input: {
                type: "text",
                name: "title",
                placeholder: "Room Title",
                id: "title"
            }
        },
        {
            label: { text: "Link" },
            input: {
                type: "text",
                name: "link",
                placeholder: "https://videochat.com/...",
                value: "https://videochat.com/room/f47ac10b-58cc-4372-a567-0e02b2c3d479",
                id: "link"
            }
        }
    ];
    
    return <Form className={ className } isLineGrid={ true } content={ content } />;
};

export default RoomOptionsForm;
